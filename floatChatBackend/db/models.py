from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from .database import Base  # <-- CORRECTED IMPORT

class Profile(Base):
    __tablename__ = "float_profiles"

    id = Column(Integer, primary_key=True, index=True)
    float_wmo_id = Column(String)
    timestamp = Column(DateTime(timezone=True))
    latitude = Column(Float)
    longitude = Column(Float)
    measurements = Column(JSON)