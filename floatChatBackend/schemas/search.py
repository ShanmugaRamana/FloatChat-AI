from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SimilarityRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, gt=0, le=20, description="Number of similar results to return")

class FilterRequest(BaseModel):
    float_wmo_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    max_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    min_lon: Optional[float] = Field(default=None, ge=-180, le=180)
    max_lon: Optional[float] = Field(default=None, ge=-180, le=180)