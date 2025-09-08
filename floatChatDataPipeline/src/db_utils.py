import logging
import chromadb
from contextlib import contextmanager
from sqlalchemy import create_engine, text, Table, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Function Definitions ---

def get_postgres_engine():
    """Creates and returns a new SQLAlchemy engine."""
    try:
        engine = create_engine(config.POSTGRES_URI, echo=False)
        logging.info("PostgreSQL engine created successfully.")
        return engine
    except Exception as e:
        logging.error(f"Failed to create PostgreSQL engine: {e}")
        raise

def init_postgres_db(engine):
    """Initializes the database by executing the schema.sql file."""
    try:
        with open('sql/schema.sql', 'r') as f:
            schema_sql = f.read()
        with engine.connect() as connection:
            connection.execute(text(schema_sql))
            connection.commit()
        logging.info("Database schema initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database schema: {e}")
        raise

@contextmanager
def get_session(engine) -> Session:
    """Provides a transactional scope around a series of database operations."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def insert_profiles_batch(session: Session, profiles_data: list[dict]) -> list[int]:
    """Inserts a batch of profiles using a fast bulk method and returns their new IDs."""
    if not profiles_data:
        return []
    
    stmt = pg_insert(float_profiles).values(profiles_data)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=['float_wmo_id', 'timestamp']
    ).returning(float_profiles.c.id)
    
    result = session.execute(stmt)
    inserted_ids = [row[0] for row in result]
    return inserted_ids

def get_processed_files(session: Session) -> set:
    """Retrieves a set of all filenames that have been successfully processed."""
    result = session.execute(text("SELECT filename FROM pipeline_tracker WHERE status = 'success';"))
    return {row[0] for row in result}

def update_file_status(session: Session, filename: str, file_hash: str, status: str):
    """Inserts or updates the status of a file in the pipeline_tracker table."""
    stmt = text("""
        INSERT INTO pipeline_tracker (filename, file_hash, status)
        VALUES (:filename, :file_hash, :status)
        ON CONFLICT (filename) DO UPDATE SET
            file_hash = EXCLUDED.file_hash,
            status = EXCLUDED.status,
            processed_at = CURRENT_TIMESTAMP;
    """)
    session.execute(stmt, {"filename": filename, "file_hash": file_hash, "status": status})

def get_chroma_client():
    """Creates and returns a ChromaDB client connected to the server."""
    try:
        client = chromadb.HttpClient(host=config.CHROMA_HOST, port=config.CHROMA_PORT)
        client.heartbeat()
        logging.info("ChromaDB client connected successfully.")
        return client
    except Exception as e:
        logging.error(f"Failed to connect to ChromaDB server: {e}")
        raise

def get_or_create_chroma_collection(client):
    """Gets a ChromaDB collection or creates it if it doesn't exist."""
    try:
        collection = client.get_or_create_collection(name=config.CHROMA_COLLECTION)
        logging.info(f"Using ChromaDB collection: '{config.CHROMA_COLLECTION}'")
        return collection
    except Exception as e:
        logging.error(f"Failed to get or create ChromaDB collection: {e}")
        raise

# --- Global Setup (Moved to the end) ---
# This block is now placed after the functions it depends on have been defined.
try:
    engine = get_postgres_engine()
    metadata = MetaData()
    float_profiles = Table('float_profiles', metadata, autoload_with=engine)
except Exception as e:
    logging.error("Failed to setup initial database objects. Ensure DB is running and accessible.")
    raise