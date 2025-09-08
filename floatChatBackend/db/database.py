from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core import config

# Create the SQLAlchemy engine using the URI from our config file.
# The engine is the central source of connectivity to the database.
engine = create_engine(config.POSTGRES_URI)

# Each instance of the SessionLocal class will be a new database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from this Base class to create each of the ORM models.
Base = declarative_base()

def get_db_session():
    """
    FastAPI dependency that creates and yields a new database session
    for each incoming request, and ensures it's closed afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()