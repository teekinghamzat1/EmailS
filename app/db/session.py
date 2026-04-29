from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# For PostgreSQL, we don't need check_same_thread: False
if "sqlite" in settings.SQLALCHEMY_DATABASE_URI:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI, 
        pool_pre_ping=True, 
        connect_args={"check_same_thread": False, "timeout": 15}
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
else:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI, 
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

