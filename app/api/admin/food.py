from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Any

from app.db.database import get_db
from app.db.models import FoodRequestLog
from app.api.admin.serializers import serialize_food_request_log

router = APIRouter()


@router.get("/food-traces")
def get_food_traces(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    total = db.query(FoodRequestLog).count()
    traces = (
        db.query(FoodRequestLog)
        .order_by(desc(FoodRequestLog.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    data = [serialize_food_request_log(t) for t in traces]
    return {"total": total, "items": data}
