from __future__ import annotations

from .common import *

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String, primary_key=True, default=lambda: generate_id("driver"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    vehicle_id = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class Trip(Base):
    __tablename__ = "trips"

    id = Column(String, primary_key=True, default=lambda: generate_id("trip"))
    customer_actor_id = Column(String, ForeignKey("actors.id"), nullable=True, index=True)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=True, index=True)
    status = Column(String, nullable=False, index=True)
    pickup_address = Column(Text, nullable=True)
    pickup_lat = Column(Float, nullable=True)
    pickup_lng = Column(Float, nullable=True)
    dropoff_address = Column(Text, nullable=True)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lng = Column(Float, nullable=True)
    estimated_fare = Column(Integer, nullable=True)
    final_fare = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class DriverStatusSnapshot(Base):
    __tablename__ = "driver_status_snapshots"

    id = Column(String, primary_key=True, default=lambda: generate_id("drvstat"))
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    battery_percent = Column(Integer, nullable=True)
    current_trip_id = Column(String, ForeignKey("trips.id"), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time, index=True)

class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(String, primary_key=True, default=lambda: generate_id("charge"))
    name = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    available_ports = Column(Integer, nullable=True)
    total_ports = Column(Integer, nullable=True)
    price_json = Column(Text, nullable=True)
    status = Column(String, default="unknown", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)
