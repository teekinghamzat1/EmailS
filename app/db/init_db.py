from app.db.base_class import Base
from app.db.session import engine
from app.models.schema import Domain, Email, Pattern # Make sure models are imported

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created.")
