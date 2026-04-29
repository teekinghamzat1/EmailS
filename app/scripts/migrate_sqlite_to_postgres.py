import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base_class import Base
from app.models.schema import Domain, Email, Pattern
from app.core.config import settings

# Source (SQLite)
SQLITE_URI = "sqlite:///./email_engine.db"
sqlite_engine = create_engine(SQLITE_URI)
SqliteSession = sessionmaker(bind=sqlite_engine)

# Destination (Postgres)
POSTGRES_URI = settings.SQLALCHEMY_DATABASE_URI
pg_engine = create_engine(POSTGRES_URI)
PgSession = sessionmaker(bind=pg_engine)

def migrate():
    print(f"Starting migration from SQLite ({SQLITE_URI}) to Postgres...")
    
    # 1. Initialize Schema in Postgres
    print("Initializing schema in Postgres...")
    Base.metadata.create_all(pg_engine)
    
    sq_db = SqliteSession()
    pg_db = PgSession()
    
    try:
        # 2. Migrate Domains
        print("Migrating Domains...")
        domains = sq_db.query(Domain).all()
        id_map = {}
        
        for i, d in enumerate(domains):
            existing = pg_db.query(Domain).filter(Domain.domain == d.domain).first()
            if not existing:
                new_d = Domain(
                    domain=d.domain,
                    status=d.status,
                    priority=d.priority,
                    source=d.source,
                    created_at=d.created_at
                )
                pg_db.add(new_d)
                pg_db.flush()
                id_map[d.id] = new_d.id
            else:
                id_map[d.id] = existing.id
            
            if (i + 1) % 1000 == 0:
                pg_db.commit()
                print(f"  Processed {i + 1}/{len(domains)} domains...")
        
        pg_db.commit()
        print(f"SUCCESS: Migrated {len(domains)} domains.")

        # 3. Migrate Emails
        print("Migrating Emails...")
        emails = sq_db.query(Email).all()
        for i, e in enumerate(emails):
            existing = pg_db.query(Email).filter(Email.email == e.email).first()
            if not existing:
                pg_domain_id = id_map.get(e.domain_id)
                if pg_domain_id:
                    new_e = Email(
                        email=e.email,
                        domain_id=pg_domain_id,
                        status=e.status,
                        confidence=e.confidence,
                        source=e.source,
                        created_at=e.created_at
                    )
                    pg_db.add(new_e)
            
            if (i + 1) % 1000 == 0:
                pg_db.commit()
                print(f"  Processed {i + 1}/{len(emails)} emails...")
        
        pg_db.commit()
        print(f"SUCCESS: Migrated {len(emails)} emails.")

        # 4. Migrate Patterns
        print("Migrating Patterns...")
        patterns = sq_db.query(Pattern).all()
        for i, p in enumerate(patterns):
            pg_domain_id = id_map.get(p.domain_id)
            if pg_domain_id:
                new_p = Pattern(
                    domain_id=pg_domain_id,
                    inferred_pattern=p.inferred_pattern,
                    source_email=p.source_email
                )
                pg_db.add(new_p)
                
            if (i + 1) % 1000 == 0:
                pg_db.commit()
                print(f"  Processed {i + 1}/{len(patterns)} patterns...")
            
        pg_db.commit()
        print(f"SUCCESS: Migrated {len(patterns)} patterns.")



        print("\nMigration COMPLETED successfully!")

    except Exception as e:
        pg_db.rollback()
        print(f"FATAL ERROR during migration: {e}")
    finally:
        sq_db.close()
        pg_db.close()

if __name__ == "__main__":
    migrate()
