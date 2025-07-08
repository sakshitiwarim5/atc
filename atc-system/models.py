from sqlalchemy import Column, Integer, String
from database import Base

class Aircraft(Base):
    __tablename__ = "aircrafts"

    id = Column(Integer, primary_key=True, index=True)
    callsign = Column(String, unique=True, index=True)
    current_altitude = Column(Integer)
    target_altitude = Column(Integer)
    current_speed = Column(Integer)
    target_speed = Column(Integer)
    current_heading = Column(Integer)
    target_heading = Column(Integer)
    status = Column(String)
