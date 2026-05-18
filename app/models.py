from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Cave(Base):
    __tablename__ = "caves"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

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


class Wall(Base):
    __tablename__ = "walls"

    id = Column(Integer, primary_key=True, index=True)
    cave_id = Column(Integer, ForeignKey("caves.id"))

    name = Column(String, nullable=False)
    orientation = Column(String, nullable=False)
    material = Column(String, nullable=False)

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