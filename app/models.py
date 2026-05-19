# app/models.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base



class Cave(Base):
    __tablename__ = "caves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    name = Column(String, nullable=False)

    region = Column(String, default="Vaud")
    altitude_m = Column(Float, default=500)

    length_m = Column(Float, nullable=False)
    width_m = Column(Float, nullable=False)
    height_m = Column(Float, nullable=False)

    buried_factor = Column(Float, default=1.0)

    walls = relationship(
        "Wall",
        back_populates="cave",
        cascade="all, delete-orphan",
    )

    zones = relationship(
        "Zone",
        back_populates="cave",
        cascade="all, delete-orphan",
    )

    energy_source = Column(String, default="electricity")
    energy_price_chf_per_kwh = Column(Float, default=0.24)
    co2_factor_kg_per_kwh = Column(Float, default=0.09)


class Wall(Base):
    __tablename__ = "walls"

    id = Column(Integer, primary_key=True, index=True)
    cave_id = Column(Integer, ForeignKey("caves.id"))

    name = Column(String, nullable=False)
    orientation = Column(String, nullable=False)
    material = Column(String, nullable=False)

    thickness_m = Column(Float, default=0.40)
    inertia_factor = Column(Float, default=1.00)

    area_m2 = Column(Float, nullable=False)
    u_value = Column(Float, nullable=False)

    cave = relationship("Cave", back_populates="walls")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    cave_id = Column(Integer, ForeignKey("caves.id"))

    name = Column(String, nullable=False)
    volume_m3 = Column(Float, nullable=False)

    target_temp_winter_c = Column(Float, nullable=False)
    target_temp_summer_c = Column(Float, nullable=False)
    target_humidity_percent = Column(Float, nullable=True)

    process_cooling_kwh = Column(Float, default=0.0)
    process_heating_kwh = Column(Float, default=0.0)

    cave = relationship("Cave", back_populates="zones")

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)

    region = Column(String, nullable=False)
    month = Column(Integer, nullable=False)

    avg_temp = Column(Float, nullable=False)
    ground_temp = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)