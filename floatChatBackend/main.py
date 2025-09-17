# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- Import this
from api import endpoints

# List of allowed origins (your frontend URLs)
origins = [
    "https://floatai.onrender.com", # Your deployed frontend
    "http://localhost:3000",      # Your local development frontend
]

# Create the main FastAPI application instance
app = FastAPI(
    title="floatChat AI Assistant",
    description="An AI assistant for oceanography questions.",
    version="1.0.0"
)

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# Include the API router
# All routes from endpoints.py will be prefixed with /api
app.include_router(endpoints.router, prefix="/api")

@app.get("/", tags=["Health Check"])
async def root():
    """
    Root endpoint for health checks.
    """
    return {"status": "ok", "message": "Welcome to the floatChat API!"}