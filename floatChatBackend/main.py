# main.py

from fastapi import FastAPI
from api import endpoints

# Create the main FastAPI application instance
app = FastAPI(
    title="floatChat AI Assistant",
    description="An AI assistant for oceanography questions, powered by Ollama.",
    version="1.0.0"
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