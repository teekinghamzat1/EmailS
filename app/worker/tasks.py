import asyncio
import logging
from app.db.session import SessionLocal
from app.models.schema import Domain, Email, Pattern
from app.scraper.crawler import crawler_engine
from app.scraper.extractor import extractor_engine
from app.validation.mx_check import validation_engine
from app.validation.smtp_check import validation_engine_deep
from app.inference.pattern_engine import pattern_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Need a wrapper to run async code inside sync task
def async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def _is_domain_match(email: str, domain: str) -> bool:
    """
    Returns True if the email belongs to the domain or any of its subdomains.
    e.g. support@mail.stripe.com matches stripe.com
    """
    email_domain = email.split('@')[1].lower()
    domain = domain.lower()
    # Exact match OR the email domain ends with .domain.com
    return email_domain == domain or email_domain.endswith('.' + domain)

def process_domain_task(domain_id: int):
    db = SessionLocal()
    domain_obj = None
    try:
        domain_obj = db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain_obj:
            return

        domain_str = domain_obj.domain
        domain_obj.status = "processing"
        db.commit()

        # 1. Crawl
        pages = async_run(crawler_engine.crawl_domain(domain_str))
        
        log.info(f"[{domain_str}] Crawled {len(pages)} pages")

        # 2. Extract Emails & Names
        raw_emails = set()
        discovered_names = set()
        for url, html in pages.items():
            # Standard email scraping
            extracted = extractor_engine.extract_from_html(html, domain_str)
            raw_emails.update(extracted)
            
            # Personnel discovery (Name scraping)
            names = extractor_engine.extract_personnel(html)
            discovered_names.update(names)

        if raw_emails or discovered_names:
            log.info(f"[{domain_str}] Extracted {len(raw_emails)} emails and {len(discovered_names)} personnel names")
        else:
            log.info(f"[{domain_str}] No data found in {len(pages)} pages")

        # 3. Validate Scraped Truth
        verified_emails = []
        for em in raw_emails:
            # Accept exact domain match OR subdomain match (e.g. mail.domain.com)
            if not _is_domain_match(em, domain_str):
                log.debug(f"[{domain_str}] Skipping off-domain email: {em}")
                continue

            is_valid, v_status = validation_engine.validate_mx(em)
            if is_valid:
                # Tier 2: Deep Handshake for verification
                deep_valid, deep_msg = validation_engine_deep.verify_mailbox(em)
                if deep_valid:
                    verified_emails.append(em)
                    log.info(f"[{domain_str}] ✓ DEEP_VERIFIED: {em}")
                else:
                    log.info(f"[{domain_str}] ⚠ MX Passed but SMTP Rejected: {em} ({deep_msg})")
                    # Still consider valid if MX passed, but with lower confidence in DB later
            else:
                log.info(f"[{domain_str}] ✗ MX Failed: {em} ({v_status})")

            # Log to DB regardless of MX result so we can see what was found
            db_email = db.query(Email).filter(Email.email == em).first()
            if not db_email:
                db_email = Email(email=em, domain_id=domain_obj.id, source="scraper")
                db.add(db_email)
            db_email.status = "valid" if is_valid else "invalid"
            db_email.confidence = 1.0 if is_valid else 0.0

        db.commit()

        # 4. Pattern Inference (ONLY if >= 1 valid exists)
        if len(verified_emails) >= 1:
            # We pick the first one to infer
            anchor = verified_emails[0]
            inferred = pattern_engine.infer_pattern(anchor)
            
            if inferred:
                # Save pattern
                db_pattern = Pattern(domain_id=domain_obj.id, inferred_pattern=inferred, source_email=anchor)
                db.add(db_pattern)
                db.commit()

                log.info(f"[{domain_str}] Pattern derived: {inferred} from {anchor}")

                # 5. Expand & Verify Candidates (Smart Synthesis)
                candidates = pattern_engine.generate_candidates(inferred, domain_str)
                for cand in candidates:
                    if db.query(Email).filter(Email.email == cand).first():
                        continue
                        
                    is_valid, v_status = validation_engine.validate_mx(cand)
                    if is_valid:
                        # Deep verify pattern candidates to ensure we aren't guessing wrong
                        deep_valid, _ = validation_engine_deep.verify_mailbox(cand)
                        if deep_valid:
                            cand_email = Email(email=cand, domain_id=domain_obj.id, source="pattern", status="valid", confidence=0.9)
                            db.add(cand_email)
                            log.info(f"[{domain_str}] Pattern candidate DEEP VERIFIED: {cand}")

                # 6. Specific Personnel Matching
                if discovered_names:
                    for name in discovered_names:
                        parts = name.split()
                        if len(parts) >= 2:
                            first, last = parts[0], parts[-1]
                            cand = pattern_engine.synthesize_from_name(first, last, inferred, domain_str)
                            if cand:
                                # Check if already exists
                                if db.query(Email).filter(Email.email == cand).first():
                                    continue
                                    
                                # Deep verify specific name candidate
                                deep_valid, _ = validation_engine_deep.verify_mailbox(cand)
                                if deep_valid:
                                    cand_email = Email(
                                        email=cand, 
                                        domain_id=domain_obj.id, 
                                        source="pattern", 
                                        status="valid", 
                                        confidence=1.0, 
                                        person_name=name
                                    )
                                    db.add(cand_email)
                                    log.info(f"[{domain_str}] Personnel match verified: {name} -> {cand}")


        domain_obj.status = "completed"
        db.commit()
        
    except Exception as e:
        log.error(f"[Domain ID {domain_id}] Task failed with error: {e}", exc_info=True)
        if domain_obj:
            try:
                domain_obj.status = "failed"
                db.commit()
            except Exception:
                pass
    finally:
        db.close()
