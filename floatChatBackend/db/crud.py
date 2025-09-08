from sqlalchemy.orm import Session
from . import models  # <-- CORRECTED IMPORT
from schemas import search as search_schema

def get_profile(db: Session, profile_id: int):
    """
    Queries the database for a profile with a specific ID.
    """
    return db.query(models.Profile).filter(models.Profile.id == profile_id).first()

def get_profiles_by_ids(db: Session, profile_ids: list[int]) -> list:
    """
    Queries the database for a list of profiles by their IDs.
    """
    if not profile_ids:
        return []
    return db.query(models.Profile).filter(models.Profile.id.in_(profile_ids)).all()

def search_profiles(db: Session, filters: search_schema.FilterRequest, skip: int = 0, limit: int = 100):
    """
    Queries the database for profiles matching a set of optional filters.
    """
    query = db.query(models.Profile)
    
    if filters.float_wmo_id:
        query = query.filter(models.Profile.float_wmo_id == filters.float_wmo_id)
    
    if filters.start_date:
        query = query.filter(models.Profile.timestamp >= filters.start_date)
        
    if filters.end_date:
        query = query.filter(models.Profile.timestamp <= filters.end_date)
        
    if filters.min_lat is not None:
        query = query.filter(models.Profile.latitude >= filters.min_lat)
        
    if filters.max_lat is not None:
        query = query.filter(models.Profile.latitude <= filters.max_lat)

    if filters.min_lon is not None:
        query = query.filter(models.Profile.longitude >= filters.min_lon)

    if filters.max_lon is not None:
        query = query.filter(models.Profile.longitude <= filters.max_lon)
        
    return query.offset(skip).limit(limit).all()