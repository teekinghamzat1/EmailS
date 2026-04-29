from typing import List, Optional

class PatternEngine:
    def infer_pattern(self, email: str) -> Optional[str]:
        """
        Infers a pattern based on a single verified email address.
        e.g., john.doe@example.com -> first.last
        """
        local_part, _ = email.split("@", 1)
        
        # We don't infer patterns for generic emails
        genres = {"info", "contact", "support", "admin", "sales", "hello", "hi"}
        if local_part in genres:
            return None
            
        if "." in local_part:
            parts = local_part.split(".")
            if len(parts) == 2:
                # john.doe -> first.last (common)
                # j.doe -> f.last
                # We can symbolize this simply as returning the literal pattern string
                p1, p2 = parts
                if len(p1) == 1 and len(p2) > 1:
                    return "f.last"
                elif len(p1) > 1 and len(p2) > 1:
                    return "first.last"
        else:
            # no dots
            if len(local_part) > 3:
                # Could be "first" or "firstlast". We will safely denote as "first"
                return "first"
                
        return None

    def synthesize_from_name(self, first: str, last: str, pattern: str, domain: str) -> Optional[str]:
        """
        Creates an email address for a specific name and pattern.
        """
        first = first.lower().strip()
        last = last.lower().strip()
        
        if pattern == "first.last":
            return f"{first}.{last}@{domain}"
        elif pattern == "f.last":
            return f"{first[0]}.{last}@{domain}"
        elif pattern == "first":
            return f"{first}@{domain}"
        elif pattern == "firstl":
            return f"{first}{last[0]}@{domain}"
        return None

    def generate_candidates(self, pattern: str, domain: str) -> List[str]:
        """
        Generates common fallback expansion candidates if a pattern is known.
        """
        test_names = [
            ("james", "smith"),
            ("mary", "johnson"),
            ("john", "williams")
        ]
        
        candidates = []
        for f, l in test_names:
            email = self.synthesize_from_name(f, l, pattern, domain)
            if email:
                candidates.append(email)
                
        return candidates

pattern_engine = PatternEngine()
