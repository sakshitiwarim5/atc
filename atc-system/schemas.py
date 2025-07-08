from pydantic import BaseModel

class AircraftCreate(BaseModel):
    callsign: str
    current_altitude: int
    target_altitude: int
    current_speed: int
    target_speed: int
    current_heading: int
    target_heading: int
    status: str

class AircraftOut(AircraftCreate):
    id: int

    class Config:
        orm_mode = True
