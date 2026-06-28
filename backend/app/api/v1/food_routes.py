from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependency import get_current_entity, get_db
from app.domains.food.recommendation_service import recommend_food


router = APIRouter()


@router.get("/recommendations")
def recommendations(
    q: str = "gợi ý món ngon",
    lat: float | None = None,
    lng: float | None = None,
    address: str | None = None,
    budget_vnd: int | None = None,
    limit: int = 8,
    db: Session = Depends(get_db),
    current_entity: dict = Depends(get_current_entity),
) -> dict:
    actor = current_entity.get("entity")
    return recommend_food(q, db=db, actor_id=getattr(actor, "id", None), lat=lat, lng=lng, address=address, budget_vnd=budget_vnd, limit=limit)
