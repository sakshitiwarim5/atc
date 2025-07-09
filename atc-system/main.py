from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine
import random

# 🚀 Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🛬 Simulated runway status (only 1 aircraft allowed at a time)
runway_busy = False

# 🛠 Dependency to get a new database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🛫 Spawn a new aircraft with random values
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

# 📋 List all aircrafts
@app.get("/aircrafts", response_model=list[schemas.AircraftOut])
def get_all_aircrafts(db: Session = Depends(get_db)):
    return db.query(models.Aircraft).all()

# 🔍 Get a specific aircraft by callsign
@app.get("/aircrafts/{callsign}", response_model=schemas.AircraftOut)
def get_aircraft_by_callsign(callsign: str, db: Session = Depends(get_db)):
    aircraft = db.query(models.Aircraft).filter(models.Aircraft.callsign == callsign).first()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    return aircraft

# ❌ Remove a random aircraft
@app.delete("/aircrafts/remove")
def remove_random_aircraft(db: Session = Depends(get_db)):
    aircrafts = db.query(models.Aircraft).all()
    if not aircrafts:
        raise HTTPException(status_code=404, detail="No aircrafts to remove")
    aircraft = random.choice(aircrafts)
    db.delete(aircraft)
    db.commit()
    return {"message": f"Aircraft {aircraft.callsign} removed successfully"}

# 🧠 Issue a command to a specific aircraft (main logic here!)
@app.post("/aircrafts/{callsign}/command", response_model=schemas.CommandResponse)
def command_aircraft(callsign: str, cmd: schemas.CommandRequest, db: Session = Depends(get_db)):
    global runway_busy

    aircraft = db.query(models.Aircraft).filter(models.Aircraft.callsign == callsign).first()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    # ✈️ CASE 1: Change altitude
    if cmd.command_type == "altitude_change":
        if 1000 <= cmd.value <= 45000:
            aircraft.target_altitude = cmd.value
            db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Altitude out of limits"}

    # 🏎️ CASE 2: Change speed
    elif cmd.command_type == "speed_change":
        if 200 <= cmd.value <= 900:
            aircraft.target_speed = cmd.value
            db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Speed out of limits"}

    # 🧭 CASE 3: Change heading
    elif cmd.command_type == "heading_change":
        if cmd.value in [0, 90, 180, 270]:
            aircraft.target_heading = cmd.value
            db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Invalid heading"}

    # 🛬 CASE 4: Land
    elif cmd.command_type == "land":
        if runway_busy:
            return {"status": "Refused", "reason": "Runway is busy"}
        if aircraft.status != "on ground":
            aircraft.status = "landing"
            aircraft.target_altitude = 0
            runway_busy = True
            db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Already on ground"}

    # 🛫 CASE 5: Take off
    elif cmd.command_type == "take_off":
        if runway_busy:
            return {"status": "Refused", "reason": "Runway is busy"}
        if aircraft.status == "on ground":
            aircraft.status = "taking off"
            aircraft.target_altitude = 30000
            runway_busy = True
            db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Already flying"}

    # 🚨 CASE 6: Emergency landing (no condition check)
    elif cmd.command_type == "emergency_land":
        aircraft.status = "landing"
        aircraft.target_altitude = 0
        aircraft.target_speed = 300
        runway_busy = True
        db.commit()
        return {"status": "Complying", "reason": "Emergency landing initiated"}

    # 🌪️ CASE 7: Weather diversion
    elif cmd.command_type == "divert":
        if cmd.value in [0, 90, 180, 270]:
            aircraft.target_heading = cmd.value
            db.commit()
            return {"status": "Complying", "reason": "Heading changed due to diversion"}
        return {"status": "Refused", "reason": "Invalid heading"}

    # ⭕ CASE 8: Holding pattern (stay in place)
    elif cmd.command_type == "hold":
        aircraft.status = "holding"
        aircraft.target_altitude = aircraft.current_altitude
        aircraft.target_speed = aircraft.current_speed
        aircraft.target_heading = aircraft.current_heading
        db.commit()
        return {"status": "Complying", "reason": "Aircraft is in holding pattern"}

    # ❌ Invalid command
    return {"status": "Refused", "reason": "Invalid command type"}

# 🔁 CASE 9: Simulate aircraft auto movement toward target
@app.put("/aircrafts/{callsign}/update_state", response_model=schemas.AircraftOut)
def update_aircraft_state(callsign: str, db: Session = Depends(get_db)):
    global runway_busy

    aircraft = db.query(models.Aircraft).filter(models.Aircraft.callsign == callsign).first()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    # Gradually move current_altitude toward target_altitude
    if aircraft.current_altitude < aircraft.target_altitude:
        aircraft.current_altitude += 1000
    elif aircraft.current_altitude > aircraft.target_altitude:
        aircraft.current_altitude -= 1000

    # Gradually move speed
    if aircraft.current_speed < aircraft.target_speed:
        aircraft.current_speed += 50
    elif aircraft.current_speed > aircraft.target_speed:
        aircraft.current_speed -= 50

    # Snap heading directly
    if aircraft.current_heading != aircraft.target_heading:
        aircraft.current_heading = aircraft.target_heading

    # ⛔ Touchdown complete
    if aircraft.status == "landing" and aircraft.current_altitude == 0:
        aircraft.status = "on ground"
        runway_busy = False

    # ✅ Take-off complete
    if aircraft.status == "taking off" and aircraft.current_altitude >= 30000:
        aircraft.status = "flying"
        runway_busy = False

    db.commit()
    db.refresh(aircraft)
    return aircraft
