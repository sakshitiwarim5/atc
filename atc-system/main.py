from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db, async_engine
import models, schemas
import random
import asyncio

app = FastAPI()

# 🚦 CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✈️ Simulated runway (only one aircraft at a time)
runway_busy = False

# 🌐 WebSocket clients
clients = set()

# 🔔 Notify all WebSocket clients to refresh
async def notify_all(message: str):
    for client in clients.copy():
        try:
            await client.send_text(message)
        except:
            clients.remove(client)

# 🔌 WebSocket connection
@app.websocket("/ws/aircrafts")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

# 🔁 Background Task for Auto Update
async def update_states():
    async with async_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    while True:
        async with get_db() as db:
            result = await db.execute(select(models.Aircraft))
            aircrafts = result.scalars().all()

            for aircraft in aircrafts:
                # Gradual Altitude
                if aircraft.current_altitude < aircraft.target_altitude:
                    aircraft.current_altitude += 1000
                elif aircraft.current_altitude > aircraft.target_altitude:
                    aircraft.current_altitude -= 1000

                # Gradual Speed
                if aircraft.current_speed < aircraft.target_speed:
                    aircraft.current_speed += 10
                elif aircraft.current_speed > aircraft.target_speed:
                    aircraft.current_speed -= 10

                # Gradual Heading
                if aircraft.current_heading < aircraft.target_heading:
                    aircraft.current_heading += 2
                elif aircraft.current_heading > aircraft.target_heading:
                    aircraft.current_heading -= 2

                # Update status based on altitude
                global runway_busy
                if aircraft.status == "landing" and aircraft.current_altitude <= 0:
                    aircraft.status = "on ground"
                    runway_busy = False
                elif aircraft.status == "taking off" and aircraft.current_altitude >= 30000:
                    aircraft.status = "flying"
                    runway_busy = False

            await db.commit()

        await notify_all("refresh")
        await asyncio.sleep(2)

# 🚀 Launch background updater on startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_states())

# --------------------------
# 📦 ROUTES
# --------------------------

# 📍 Spawn new aircraft
@app.post("/aircrafts/spawn", response_model=schemas.AircraftOut)
async def spawn_aircraft(db: AsyncSession = Depends(get_db)):
    callsign = f"FLT{random.randint(100, 999)}"
    aircraft = models.Aircraft(
        callsign=callsign,
        current_altitude=random.randint(20000, 30000),
        target_altitude=random.randint(30000, 40000),
        current_speed=random.randint(300, 600),
        target_speed=random.randint(300, 600),
        current_heading=random.choice([0, 90, 180, 270]),
        target_heading=random.choice([0, 90, 180, 270]),
        status="flying"
    )
    db.add(aircraft)
    await db.commit()
    await db.refresh(aircraft)
    return aircraft

# 📍 List all aircrafts
@app.get("/aircrafts", response_model=list[schemas.AircraftOut])
async def get_aircrafts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Aircraft))
    return result.scalars().all()

# 📍 Command an aircraft
@app.post("/aircrafts/{callsign}/command", response_model=schemas.CommandResponse)
async def command_aircraft(callsign: str, cmd: schemas.CommandRequest, db: AsyncSession = Depends(get_db)):
    global runway_busy

    result = await db.execute(select(models.Aircraft).filter_by(callsign=callsign))
    aircraft = result.scalar_one_or_none()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    if cmd.command_type == "altitude_change":
        if 1000 <= cmd.value <= 45000:
            aircraft.target_altitude = cmd.value
            await db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Altitude out of limits"}

    elif cmd.command_type == "speed_change":
        if 200 <= cmd.value <= 900:
            aircraft.target_speed = cmd.value
            await db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Speed out of limits"}

    elif cmd.command_type == "heading_change":
        if cmd.value in [0, 90, 180, 270]:
            aircraft.target_heading = cmd.value
            await db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Invalid heading"}

    elif cmd.command_type == "land":
        if runway_busy:
            return {"status": "Refused", "reason": "Runway is busy"}
        if aircraft.status != "on ground":
            aircraft.status = "landing"
            aircraft.target_altitude = 0
            runway_busy = True
            await db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Already on ground"}

    elif cmd.command_type == "take_off":
        if runway_busy:
            return {"status": "Refused", "reason": "Runway is busy"}
        if aircraft.status == "on ground":
            aircraft.status = "taking off"
            aircraft.target_altitude = 30000
            runway_busy = True
            await db.commit()
            return {"status": "Complying"}
        return {"status": "Refused", "reason": "Already flying"}

    elif cmd.command_type == "emergency_land":
        aircraft.status = "landing"
        aircraft.target_altitude = 0
        aircraft.target_speed = 300
        runway_busy = True
        await db.commit()
        return {"status": "Complying", "reason": "Emergency landing initiated"}

    elif cmd.command_type == "divert":
        if cmd.value in [0, 90, 180, 270]:
            aircraft.target_heading = cmd.value
            await db.commit()
            return {"status": "Complying", "reason": "Heading changed due to diversion"}
        return {"status": "Refused", "reason": "Invalid heading"}

    elif cmd.command_type == "hold":
        aircraft.status = "holding"
        aircraft.target_altitude = aircraft.current_altitude
        aircraft.target_speed = aircraft.current_speed
        aircraft.target_heading = aircraft.current_heading
        await db.commit()
        return {"status": "Complying", "reason": "Aircraft is in holding pattern"}

    return {"status": "Refused", "reason": "Invalid command type"}
