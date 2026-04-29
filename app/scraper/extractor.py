import re
import urllib.parse
from bs4 import BeautifulSoup
from typing import Set

# Common list of disposable or generic unhelpful emails
DISPOSABLE_DOMAINS = {"mailinator.com", "yopmail.com", "guerrillamail.com"}
GENERIC_PREFIXES = {"info", "contact", "support", "admin", "sales", "hello", "hi"}

class EmailExtractor:
    def __init__(self):
        # Extremely robust regex for email matching from raw text
        self.email_regex = re.compile(
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            re.IGNORECASE
        )

    def extract_from_html(self, html: str, target_domain: str) -> Set[str]:
        """
        Extracts emails from an HTML string, preferring emails that match the target_domain.
        Returns a set of extracted valid emails.
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Pull text from the page (ignoring scripts, styles)
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
            
        text = soup.get_text()
        
        emails = set()
        
        # Also check mailto links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].lower()
            if href.startswith("mailto:"):
                # Clean mailto: string (it could have ?subject=)
                clean_email = urllib.parse.unquote(href[7:].split('?')[0]).strip()
                emails.add(clean_email)
                
        # Regex search over raw text (protects against heavily styled emails)
        matches = self.email_regex.findall(text)
        for m in matches:
            emails.add(m.strip().lower())
            
        # Filter and normalize
        valid_emails = set()
        for e in emails:
            e = e.strip().lower()
            if not getattr(self.email_regex.match(e), 'group', None):
                continue
                
            local_part, domain_part = e.split("@", 1)
            
            # Simple filtration rules (PRD Rule: must match domain OR be legit public business email)
            # To keep it safe and focus on our specific scraping target:
            if domain_part in DISPOSABLE_DOMAINS:
                continue
                
            # Check length to prevent massive regex false positive string captures
            if len(e) > 100 or len(e) < 5:
                continue
                
            valid_emails.add(e)
            
        return valid_emails

    def extract_personnel(self, html: str) -> Set[str]:
        """
        Attempts to find employee names in the HTML through heuristic analysis.
        """
        names = set()
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Look for highly likely name containers
        # Many companies use card-titles, member-names, etc.
        containers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'span', 'p', 'strong'], 
                                  class_=re.compile(r'name|member|staff|person|title|bio', re.I))
        
        for c in containers:
            text = c.get_text().strip()
            # Simple heuristic: must be 2-3 words, Title Cased, 3-30 chars total
            if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+( [A-Z][a-z]+)?$', text):
                names.add(text)
        
        # 2. Fallback: scan for standalone names in the body if we are on a likely team page
        # This is more dangerous (noise) but helpful for minimalist sites
        if not names:
            text_nodes = soup.find_all(text=True)
            for node in text_nodes:
                if node.parent.name in ['script', 'style', 'nav', 'header', 'footer']:
                    continue
                text = str(node).strip()
                if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', text) and len(text) < 25:
                    names.add(text)
                    
        return names

extractor_engine = EmailExtractor()
