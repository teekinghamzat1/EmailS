import dns.resolver
from typing import Tuple

class ValidationEngine:
    def validate_mx(self, email: str) -> Tuple[bool, str]:
        """
        Validates the domain of an email address by checking its MX records.
        Returns a tuple of (is_valid, status_string).
        """
        if "@" not in email:
            return False, "invalid_syntax"
            
        domain = email.split("@")[1]
        
        try:
            # Query for MX records
            records = dns.resolver.resolve(domain, 'MX')
            if records and len(records) > 0:
                return True, "valid"
            return False, "invalid_mx_empty"
        except dns.resolver.NXDOMAIN:
            return False, "invalid_domain_does_not_exist"
        except dns.resolver.NoAnswer:
            return False, "invalid_no_mx_record"
        except dns.exception.Timeout:
            return False, "timeout"
        except Exception as e:
            return False, f"error_{str(e)[:20]}"

validation_engine = ValidationEngine()
