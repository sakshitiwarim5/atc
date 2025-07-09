from pydantic import BaseModel
from typing import Optional

# Aircraft Create input schema
class AircraftCreate(BaseModel):
    callsign: str
    current_altitude: int
    target_altitude: int
    current_speed: int
    target_speed: int
    current_heading: int
    target_heading: int
    status: str

# Aircraft response schema
class AircraftOut(AircraftCreate):
    id: int

    class Config:
        orm_mode = True

# Command request schema
class CommandRequest(BaseModel):
    command_type: str
    value: Optional[int] = None

# Command response schema
class CommandResponse(BaseModel):
    status: str
    reason: Optional[str] = None
