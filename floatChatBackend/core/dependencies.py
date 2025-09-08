from functools import lru_cache
from sentence_transformers import SentenceTransformer
from db import vector_search # <-- CORRECTED IMPORT

class SearchServices:
    """A container for search-related services loaded once."""
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        # CORRECTED CALLS:
        chroma_client = vector_search.get_chroma_client()
        self.chroma_collection = vector_search.get_or_create_chroma_collection(chroma_client)

@lru_cache(maxsize=1)
def get_search_services() -> SearchServices:
    """
    Dependency that provides a cached instance of the search services.
    lru_cache ensures the models and clients are only loaded once.
    """
    return SearchServices()