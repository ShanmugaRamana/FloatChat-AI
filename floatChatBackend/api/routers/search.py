from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import List

from db import crud, database, vector_search
from schemas import profile as profile_schema
from schemas import search as search_schema
from core.dependencies import get_search_services, SearchServices

router = APIRouter()

@router.post(
    "/similar",
    response_model=List[profile_schema.Profile],
    summary="Find profiles similar to a text query"
)
async def search_similar_profiles(
    request: search_schema.SimilarityRequest,
    db: Session = Depends(database.get_db_session),
    search_services: SearchServices = Depends(get_search_services)
):
    """
    Performs a semantic search using a natural language query. It finds the most
    conceptually similar data points in the database.
    """
    similar_profiles = await vector_search.find_similar_profiles(
        query=request.query,
        db=db,
        chroma_collection=search_services.chroma_collection,
        embedding_model=search_services.embedding_model,
        top_k=request.top_k
    )
    return similar_profiles

@router.post(
    "/filter",
    response_model=List[profile_schema.Profile],
    summary="Find profiles using structured filters"
)
def search_profiles_by_filter(
    filters: search_schema.FilterRequest = Body(...),
    db: Session = Depends(database.get_db_session),
    skip: int = 0,
    limit: int = 100
):
    """
    Performs a structured search based on specific criteria like date range,
    geographic bounding box, and float ID.
    """
    profiles = crud.search_profiles(db=db, filters=filters, skip=skip, limit=limit)
    return profiles