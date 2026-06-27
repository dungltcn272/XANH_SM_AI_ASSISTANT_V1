from __future__ import annotations

from .common import *

class ExecutiveInsightReport(Base):
    __tablename__ = "executive_insight_reports"

    id = Column(String, primary_key=True, default=lambda: generate_id("insight"))
    title = Column(String, nullable=False)
    region = Column(String, nullable=True, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    insight_type = Column(String, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    data_json = Column(Text, nullable=True)
    created_by_run_id = Column(String, ForeignKey("assistant_runs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String, primary_key=True, default=lambda: generate_id("evalrun"))
    run_name = Column(String, index=True, nullable=False)
    dataset_name = Column(String, default="golden_50")
    model_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    total_cases = Column(Integer, default=0)
    status = Column(String, default="completed", index=True)
    average_latency_sec = Column(Float, default=0)
    recall_5 = Column(Float, default=0)
    recall_10 = Column(Float, default=0)
    mrr = Column(Float, default=0)
    ndcg_5 = Column(Float, default=0)
    faithfulness = Column(Float, default=0)
    correctness = Column(Float, default=0)
    relevancy = Column(Float, default=0)
    metrics_json = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
