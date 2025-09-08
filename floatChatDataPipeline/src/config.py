import os
from dotenv import load_dotenv

load_dotenv()


POSTGRES_URI = os.getenv("POSTGRES_URI")
if not POSTGRES_URI:
    raise ValueError("POSTGRES_URI environment variable not set. Please check your .env file.")



CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "ocean_profiles")

try:
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
except ValueError:
    raise ValueError("CHROMA_PORT must be a valid integer. Please check your .env file.")