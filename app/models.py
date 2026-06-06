# app/models.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    caves = relationship("Cave", back_populates="user")

class Cave(Base):
    __tablename__ = "caves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    user = relationship("User", back_populates="caves")

    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    use_dynamic_weather = Column(Boolean, default=False)

    region = Column(String, default="Vaud")
    altitude_m = Column(Float, default=500)

    length_m = Column(Float, nullable=False)
    width_m = Column(Float, nullable=False)
    height_m = Column(Float, nullable=False)

    buried_factor = Column(Float, default=1.0)

    ventilation_rate_ach = Column(Float, default=0.2)
    ventilation_enabled = Column(Boolean, default=True)

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

    renovation_scenarios = relationship(
        "RenovationScenarioDB",
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
    x_m = Column(Float, default=0)
    y_m = Column(Float, default=0)

    width_m = Column(Float, default=1)
    length_m = Column(Float, default=1)

    target_temp_winter_c = Column(Float, nullable=False)
    target_temp_summer_c = Column(Float, nullable=False)
    target_humidity_percent = Column(Float, nullable=True)

    process_cooling_kwh = Column(Float, default=0.0)
    process_heating_kwh = Column(Float, default=0.0)

    cave = relationship("Cave", back_populates="zones")

    process_heating_start_month = Column(Integer, default=1)
    process_heating_end_month = Column(Integer, default=12)
    process_cooling_start_month = Column(Integer, default=1)
    process_cooling_end_month = Column(Integer, default=12)

    monthly_targets = relationship(
        "ZoneMonthlyTarget",
        back_populates="zone",
        cascade="all, delete-orphan",
        order_by="ZoneMonthlyTarget.month",
    )

class ZoneMonthlyTarget(Base):
    __tablename__ = "zone_monthly_targets"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)

    month = Column(Integer, nullable=False)
    target_temp_c = Column(Float, nullable=False)
    target_humidity_percent = Column(Float, default=75)
    phase = Column(String, default="standard")

    zone = relationship("Zone", back_populates="monthly_targets")

    __table_args__ = (
        UniqueConstraint("zone_id", "month", name="uq_zone_monthly_target"),
    )

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)

    region = Column(String, nullable=False)
    month = Column(Integer, nullable=False)

    avg_temp = Column(Float, nullable=False)
    ground_temp = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)

class RenovationScenarioDB(Base):
    __tablename__ = "renovation_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    cave_id = Column(Integer, ForeignKey("caves.id", ondelete="CASCADE"))

    name = Column(String, nullable=False)
    investment_chf = Column(Float, default=0)

    roof_reduction_percent = Column(Float, default=0)
    walls_reduction_percent = Column(Float, default=0)
    floor_reduction_percent = Column(Float, default=0)

    cave = relationship("Cave", back_populates="renovation_scenarios")