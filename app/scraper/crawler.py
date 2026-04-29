import httpx
import logging
from typing import Optional, Dict
from app.core.config import settings

log = logging.getLogger(__name__)

class CrawlerEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        self.proxy = settings.PROXY_URL if settings.PROXY_URL and settings.PROXY_URL.strip() else None
    
    async def fetch_page(self, url: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False, proxy=self.proxy) as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.text
                return None
        except RuntimeError:
            # httpx's internal thread pool shuts down on server reload — suppress cleanly
            return None
        except httpx.HTTPError as e:
            log.debug(f"HTTP Error fetching {url}: {e}")
            return None
        except Exception as e:
            log.debug(f"Unexpected Error fetching {url}: {type(e).__name__} - {e}")
            return None

    async def crawl_domain(self, domain: str) -> Dict[str, str]:
        """
        Crawls the homepage, /about, and /contact pages of a domain.
        Returns a dict of url to html string.
        """
        pages = {}
        paths_to_crawl = [
            "",
            "/contact",
            "/contact-us",
            "/about",
            "/about-us",
            "/team",
            "/our-team",
            "/people",
            "/staff",
            "/leadership",
            "/company",
            "/who-we-are",
        ]
        
        for path in paths_to_crawl:
            url = f"https://{domain}{path}"
            html = await self.fetch_page(url)
            if html:
                pages[url] = html
            else:
                # Try http if https fails
                url_http = f"http://{domain}{path}"
                html = await self.fetch_page(url_http)
                if html:
                    pages[url_http] = html
                    
        return pages

crawler_engine = CrawlerEngine()
