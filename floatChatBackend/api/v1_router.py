from fastapi import APIRouter
from api.routers import search, profiles, chat

# Create the main router for the v1 API
api_router = APIRouter()

# Include the search endpoints, adding a '/search' prefix and a 'Search' tag for documentation
api_router.include_router(search.router, prefix="/search", tags=["Search"])

# Include the profile endpoints, adding a '/profiles' prefix and a 'Profiles' tag for documentation
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])

# Include the chat endpoints, adding a '/chat' prefix and a 'Chat' tag for documentation
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])