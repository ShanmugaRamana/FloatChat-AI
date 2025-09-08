# In schemas/profile.py
from pydantic import BaseModel, ConfigDict # <-- Import ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class Profile(BaseModel):
    id: int
    float_wmo_id: Optional[str] = None
    timestamp: datetime
    latitude: float
    longitude: float
    measurements: Dict[str, Any]

    # FIX: Use model_config with from_attributes=True for Pydantic v2
    model_config = ConfigDict(from_attributes=True)