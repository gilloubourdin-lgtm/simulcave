# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import cave, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SimulCave")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(cave.router)