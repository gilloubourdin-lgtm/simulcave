# app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import auth, cave


app = FastAPI(
    title="SimulCave",
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

app.include_router(auth.router)
app.include_router(cave.router)