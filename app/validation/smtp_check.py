import socket
import smtplib
import dns.resolver
import logging
from typing import Tuple, Optional

log = logging.getLogger(__name__)

class SMTPValidationEngine:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _get_mx_server(self, domain: str) -> Optional[str]:
        """Fetch primary MX record for a domain."""
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_record = sorted(records, key=lambda r: r.preference)[0].exchange
            return str(mx_record).rstrip('.')
        except Exception as e:
            log.debug(f"MX lookup failed for {domain}: {e}")
            return None

    def verify_mailbox(self, email: str, sender: str = "verify@truth-engine.com") -> Tuple[bool, str]:
        """
        Performs a deep SMTP handshake to verify if a mailbox actually exists.
        Returns (is_valid, status_message).
        """
        domain = email.split('@')[1]
        mx_server = self._get_mx_server(domain)
        
        if not mx_server:
            return False, "No MX records found"

        try:
            # Use a longer timeout for the initial connection
            server = smtplib.SMTP(timeout=self.timeout)
            server.connect(mx_server)
            
            # 1. HELO/EHLO
            status, _ = server.helo("intelligence-engine.local")
            if status != 250:
                server.quit()
                return False, f"HELO failed: {status}"

            # 2. MAIL FROM
            status, _ = server.mail(sender)
            if status != 250:
                server.quit()
                return False, f"MAIL FROM rejected: {status}"

            # 3. RCPT TO (The core verification step)
            status, message = server.rcpt(email)
            server.quit()

            # 250 = Accepted, 251 = Will Forward
            if status in [250, 251]:
                return True, "Mailbox accepted"
            elif status == 550:
                return False, "Mailbox does not exist (550)"
            else:
                return False, f"Server response: {status} - {message}"

        except (socket.timeout, socket.error) as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            log.debug(f"SMTP verification failed for {email}: {e}")
            return False, f"Internal Error: {str(e)}"

validation_engine_deep = SMTPValidationEngine()
