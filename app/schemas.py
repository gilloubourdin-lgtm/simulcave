# app/schemas.py

from pydantic import BaseModel


class CaveCreate(BaseModel):
    name: str
    length_m: float
    width_m: float
    height_m: float
    buried_factor: float


class WallCreate(BaseModel):
    name: str
    orientation: str
    material: str
    area_m2: float
    u_value: float


class ZoneCreate(BaseModel):
    name: str
    volume_m3: float
    target_temp_winter_c: float
    target_temp_summer_c: float
    target_humidity_percent: float | None = None
    process_cooling_kwh: float = 0
    process_heating_kwh: float = 0