from core.db.database import Base, engine
from models.accounts.users import CustomerUser

def init_db():
    """Initialize the database by creating all tables."""
    print("Starting database initialization...")
    print("Available tables before creation:", Base.metadata.tables.keys())
    
    # Create all tables
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    print("Created tables:", Base.metadata.tables.keys())

if __name__ == "__main__":
    init_db() 