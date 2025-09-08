from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import crud, database, models
from schemas import profile as profile_schema

router = APIRouter()

@router.get(
    "/{profile_id}",
    response_model=profile_schema.Profile,
    summary="Get a Single Profile by ID"
)
def read_profile(profile_id: int, db: Session = Depends(database.get_db_session)):
    """
    Retrieve a single oceanographic data profile from the database using its unique ID.
    
    - **profile_id**: The unique integer ID of the profile.
    - **Returns**: A single profile object if found.
    - **Raises**: A 404 error if the profile is not found.
    """
    db_profile = crud.get_profile(db=db, profile_id=profile_id)
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile