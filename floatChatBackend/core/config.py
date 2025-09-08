import os
from dotenv import load_dotenv

# This function finds and loads the .env file from the project's root directory,
# making its variables accessible to the application.
load_dotenv()

# --- PostgreSQL Configuration ---
POSTGRES_URI = os.getenv("POSTGRES_URI")
if not POSTGRES_URI:
    raise ValueError("POSTGRES_URI environment variable not set. Please check your .env file.")

# --- OpenRouter LLM Service Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set. Please check your .env file.")

# --- ChromaDB Configuration ---
# These are needed by the dependency loader to connect to the vector database.
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
try:
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
except ValueError:
    raise ValueError("CHROMA_PORT must be a valid integer. Please check your .env file.")