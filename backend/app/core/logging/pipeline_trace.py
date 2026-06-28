from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AiTraceEvent, AssistantRun, get_vn_time


logger = logging.getLogger("pipeline")


@dataclass
class PipelineTracer:
    run_id: str
    conversation_id: str | None
    persona_id: str
    db: Session | None = None
    started_at: float = field(default_factory=time.perf_counter)
    events: list[dict[str, Any]] = field(default_factory=list)
    run_row_enabled: bool = False

    def start_run(self, *, actor_id: str | None = None) -> None:
        if self.db is None or not self.conversation_id:
            return
        try:
            self.db.add(
                AssistantRun(
                    id=self.run_id,
                    conversation_id=self.conversation_id,
                    actor_id=actor_id,
                    persona_id=self.persona_id,
                    status="running",
                )
            )
            self.db.flush()
            self.run_row_enabled = True
        except Exception as exc:
            try:
                self.db.rollback()
            except Exception:
                pass
            logger.warning("run=%s assistant_run_create_failed=%s", self.run_id, exc)

    def finish_run(self, *, intent: str | None, status: str = "completed", latency_ms: float = 0.0, model_name: str | None = None) -> None:
        if self.db is None or not self.run_row_enabled:
            return
        try:
            row = self.db.query(AssistantRun).filter(AssistantRun.id == self.run_id).first()
            if row:
                row.intent = intent
                row.status = status
                row.latency_ms = latency_ms
                row.model_name = model_name
                row.finished_at = get_vn_time()
                self.db.flush()
        except Exception as exc:
            try:
                self.db.rollback()
            except Exception:
                pass
            logger.warning("run=%s assistant_run_finish_failed=%s", self.run_id, exc)

    def emit(self, node: str, event: str, *, level: str = "INFO", **payload: Any) -> None:
        elapsed_ms = (time.perf_counter() - self.started_at) * 1000
        clean_payload = {key: value for key, value in payload.items() if value is not None}
        entry = {
            "node": node,
            "event": event,
            "level": level,
            "elapsed_ms": round(elapsed_ms, 1),
            "payload": clean_payload,
        }
        self.events.append(entry)
        logger.log(
            getattr(logging, level.upper(), logging.INFO),
            "run=%s conv=%s persona=%s node=%s event=%s %.1fms payload=%s",
            self.run_id,
            self.conversation_id,
            self.persona_id,
            node,
            event,
            elapsed_ms,
            json.dumps(clean_payload, ensure_ascii=False, default=str),
        )
        if self.db is None:
            return
        try:
            self.db.add(
                AiTraceEvent(
                    run_id=self.run_id if self.run_row_enabled else None,
                    conversation_id=self.conversation_id,
                    persona_id=self.persona_id,
                    node=node,
                    event=event,
                    level=level.upper(),
                    payload_json=json.dumps({"run_id": self.run_id, "elapsed_ms": elapsed_ms, **clean_payload}, ensure_ascii=False, default=str),
                )
            )
            self.db.flush()
        except Exception as exc:
            try:
                self.db.rollback()
            except Exception:
                pass
            logger.warning("run=%s node=%s event=%s db_trace_failed=%s", self.run_id, node, event, exc)

    def active_layers(self) -> list[str]:
        layers: list[str] = []
        for event in self.events:
            node = str(event.get("node") or "")
            if node and node not in layers:
                layers.append(node)
        return layers

    def summary(self) -> list[dict[str, Any]]:
        return self.events
