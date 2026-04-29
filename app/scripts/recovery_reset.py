
import sys
import os
import logging
from sqlalchemy import text

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.schema import Domain, Email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Recovery")

def run_recovery():
    db = SessionLocal()
    try:
        logger.info("Starting recovery process...")
        
        # We find domains that are completed but have no emails.
        # This is the clear indicator of the bug impact.
        
        # Subquery for domains with at least one email
        subquery = db.query(Email.domain_id).distinct()
        
        # Domains to reset: completed status AND not in the email subquery
        to_reset_query = db.query(Domain).filter(
            Domain.status == 'completed',
            ~Domain.id.in_(subquery)
        )
        
        total_to_reset = to_reset_query.count()
        logger.info(f"Found {total_to_reset} domains marked as 'completed' with 0 emails.")
        
        if total_to_reset > 0:
            logger.info("Resetting statuses to 'queued'...")
            # We do it in batches to avoid locking the DB for too long if it's large
            batch_size = 5000
            processed = 0
            
            while processed < total_to_reset:
                batch = to_reset_query.limit(batch_size).all()
                if not batch:
                    break
                
                for d in batch:
                    d.status = 'queued'
                
                db.commit()
                processed += len(batch)
                logger.info(f"Reset {processed}/{total_to_reset} domains...")
            
            logger.info("Recovery complete. All failed domains are back in queue.")
        else:
            logger.info("No domains found matching the recovery criteria.")

    except Exception as e:
        logger.error(f"Recovery failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_recovery()
