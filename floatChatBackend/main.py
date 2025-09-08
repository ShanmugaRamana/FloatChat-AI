from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1_router import api_router

# Create the main FastAPI application instance
app = FastAPI(
    title="FloatChat AI Backend",
    description="API for querying oceanographic data with AI.",
    version="1.0.0"
)

# --- CORS (Cross-Origin Resource Sharing) ---
# This allows your web frontend (running on a different domain)
# to communicate with this backend.
# For production, you should restrict origins to your actual frontend's URL.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# Include the main router for version 1 of the API.
# All routes defined in v1_router will be prefixed with /api/v1.
app.include_router(api_router, prefix="/api/v1")

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "FloatChat AI Backend is running"}