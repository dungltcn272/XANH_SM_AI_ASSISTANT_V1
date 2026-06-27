from __future__ import annotations

from .common import *

class OperationalMetricSnapshot(Base):
    __tablename__ = "operational_metric_snapshots"

    id = Column(String, primary_key=True, default=lambda: generate_id("opsmetric"))
    metric_date = Column(Date, nullable=False, index=True)
    region = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    dimension_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class FraudSignal(Base):
    __tablename__ = "fraud_signals"

    id = Column(String, primary_key=True, default=lambda: generate_id("fraud"))
    actor_id = Column(String, ForeignKey("actors.id"), nullable=True)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=True)
    trip_id = Column(String, ForeignKey("trips.id"), nullable=True)
    signal_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    score = Column(Float, default=0.0)
    evidence_json = Column(Text, nullable=True)
    status = Column(String, default="new", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
