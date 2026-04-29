import os
import httpx
import zipfile
import gzip
import io
import asyncio
from typing import List
import concurrent.futures
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models.schema import Domain, Email, SystemSettings
from app.worker.tasks import process_domain_task
import threading
import time

TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
# Latest Common Crawl Web Graph (as of April 2026)
CC_URL = "https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2026-jan-feb-mar/domain/cc-main-2026-jan-feb-mar-domain-names.txt.gz"

class AutoDiscoveryEngine:
    def __init__(self):
        self.is_running = False
        # Scale up to 50+ concurrent threads now that we are on PostgreSQL
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)
        self._submitted_ids = set()

    def _check_limits(self) -> bool:
        """
        Returns True if the system is allowed to extraction more data based on limits and activity switch.
        """
        db = SessionLocal()
        try:
            settings = db.query(SystemSettings).first()
            if not settings or not settings.is_active:
                return False

            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)
            start_of_day = datetime(now.year, now.month, now.day)

            # Monthly check
            monthly_count = db.query(Email).filter(Email.created_at >= start_of_month).count()
            if monthly_count >= settings.monthly_limit:
                print(f"[Engine-Guard] Monthly limit reached ({monthly_count}/{settings.monthly_limit}). Pausing.")
                return False

            # Daily check
            daily_count = db.query(Email).filter(Email.created_at >= start_of_day).count()
            if daily_count >= settings.daily_limit:
                print(f"[Engine-Guard] Daily limit reached ({daily_count}/{settings.daily_limit}). Pausing.")
                return False

            return True
        except Exception as e:
            print(f"[Engine-Guard] Error checking limits: {e}")
            return False
        finally:
            db.close()

    def download_and_feed_tranco(self):
        """
        Stream Tranco Top 1M list.
        """
        print("[Auto-Discovery] Starting dataset download from Tranco...")
        try:
            with httpx.Client(timeout=60.0, follow_redirects=True) as client:
                response = client.get(TRANCO_URL)
                response.raise_for_status()

                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                csv_filename = zip_file.namelist()[0]
                
                print(f"[Auto-Discovery] Downloaded Tranco {csv_filename}. Feeding...")
                with zip_file.open(csv_filename) as f:
                    batch = []
                    for line in f:
                        while self.is_running and not self._check_limits():
                            time.sleep(60) # Sleep if limits reached

                        if not self.is_running:
                            break
                            
                        decoded_line = line.decode('utf-8').strip()
                        if "," in decoded_line:
                            _, domain_name = decoded_line.split(",", 1)
                            domain_name = domain_name.split("/")[0].lower()
                            batch.append(domain_name)

                            if len(batch) >= 20:
                                self._push_batch(batch)
                                batch = []
                                time.sleep(0.1)
                                
                    if batch:
                        self._push_batch(batch)

        except Exception as e:
            print(f"[Auto-Discovery] Tranco Error: {e}")

    def download_and_feed_cc(self):
        """
        Stream Common Crawl Domain List (IndefiniteSource).
        """
        print("[Auto-Discovery] Starting dataset stream from Common Crawl...")
        try:
            # Using stream=True for large GZ file
            with httpx.stream("GET", CC_URL, timeout=60.0, follow_redirects=True) as response:
                response.raise_for_status()
                
                # Wrap the stream in GzipFile for line-by-line reading
                with gzip.GzipFile(fileobj=response.raw) as f:
                    batch = []
                    for line in f:
                        while self.is_running and not self._check_limits():
                            time.sleep(60)

                        if not self.is_running:
                            break
                            
                        domain_name = line.decode('utf-8').strip().lower()
                        if domain_name:
                            batch.append(domain_name)

                            if len(batch) >= 20:
                                self._push_batch(batch)
                                batch = []
                                time.sleep(0.1)
                                
                    if batch:
                        self._push_batch(batch)

        except Exception as e:
            print(f"[Auto-Discovery] Common Crawl Error: {e}")

    def poll_queued_domains(self):
        """
        Periodically polls the DB for domains in 'queued' status.
        """
        print("[Queue-Poller] Starting prioritize poll loop...")
        while self.is_running:
            if not self._check_limits():
                time.sleep(60)
                continue

            db = SessionLocal()
            try:
                queued = db.query(Domain).filter(
                    Domain.status == "queued"
                ).limit(100).all()

                if not queued:
                    time.sleep(10)
                    continue

                for d in queued:
                    if not self.is_running:
                        break
                    if d.id not in self._submitted_ids:
                        print(f"[Queue-Poller] Dispatched existing Domain: {d.domain}")
                        self._submitted_ids.add(d.id)
                        try:
                            self.executor.submit(process_domain_task, d.id)
                        except RuntimeError:
                            break
                
                time.sleep(5)
            except Exception as e:
                print(f"[Queue-Poller] Error: {e}")
                time.sleep(10)
            finally:
                db.close()

    def _push_batch(self, domains: List[str]):
        """
        Saves new domains and submits them for processing.
        """
        db = SessionLocal()
        try:
            docs_to_process = []
            for d in domains:
                existing = db.query(Domain).filter(Domain.domain == d).first()
                if not existing:
                    new_domain = Domain(domain=d, source="autonomous")
                    db.add(new_domain)
                    db.commit()
                    db.refresh(new_domain)
                    docs_to_process.append(new_domain.id)

            for doc_id in docs_to_process:
                if not self.is_running:
                    break
                if doc_id not in self._submitted_ids:
                    self._submitted_ids.add(doc_id)
                    try:
                        self.executor.submit(process_domain_task, doc_id)
                    except RuntimeError:
                        break
                    
        except Exception as e:
            print(f"[Auto-Discovery] Batch Error: {e}")
        finally:
            db.close()

    def start_loop(self):
        if self.is_running:
            return
        self.is_running = True
        
        # 1. Start Tranco Discovery Thread
        threading.Thread(target=self.download_and_feed_tranco, daemon=True).start()
        
        # 2. Start Common Crawl Discovery Thread
        threading.Thread(target=self.download_and_feed_cc, daemon=True).start()
        
        # 3. Start Priority Queue Poller Thread
        threading.Thread(target=self.poll_queued_domains, daemon=True).start()

    def stop_loop(self):
        self.is_running = False
        self.executor.shutdown(wait=False)

discovery_engine = AutoDiscoveryEngine()
