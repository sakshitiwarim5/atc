from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine
import random

# Pehle table create kar do
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/aircrafts/spawn", response_model=schemas.AircraftOut)
def spawn_aircraft(db: Session = Depends(get_db)):
    callsign = f"FLT{random.randint(100, 999)}"
    aircraft = models.Aircraft(
        callsign=callsign,
        current_altitude=random.randint(20000, 40000),
        target_altitude=random.randint(20000, 40000),
        current_speed=random.randint(300, 600),
        target_speed=random.randint(300, 600),
        current_heading=random.choice([0, 90, 180, 270]),
        target_heading=random.choice([0, 90, 180, 270]),
        status="flying"
    )
    db.add(aircraft)
    db.commit()
    db.refresh(aircraft)
    return aircraft
