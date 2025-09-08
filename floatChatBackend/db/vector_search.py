import logging
import chromadb
from sqlalchemy.orm import Session
from db import crud
from core import config
from typing import Optional, List

# --- ChromaDB Connection Utilities ---

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
        collection = client.get_or_create_collection(name="ocean_profiles")
        logging.info(f"Using ChromaDB collection: 'ocean_profiles'")
        return collection
    except Exception as e:
        logging.error(f"Failed to get or create ChromaDB collection: {e}")
        raise

# --- Search Functionality ---

# In db/vector_search.py

async def find_similar_profiles(
    query: str, 
    db: Session, 
    chroma_collection, 
    embedding_model, 
    top_k: int = 5,
    filter_ids: Optional[List[int]] = None
) -> list:
    """
    Finds similar profiles, optionally filtering within a specific set of IDs.
    """
    query_embedding = embedding_model.encode(query).tolist()
    
    # NEW: If filter_ids are provided, add a 'where' clause to the ChromaDB query
    where_filter = None
    if filter_ids:
        where_filter = {"postgres_id": {"$in": filter_ids}}

    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter # Pass the filter to ChromaDB
    )
    
    if not results['ids'][0]:
        return []
    
    profile_ids = [int(meta['postgres_id']) for meta in results['metadatas'][0]]
    
    if not profile_ids:
        return []
        
    profiles = crud.get_profiles_by_ids(db=db, profile_ids=profile_ids)
    return profiles
