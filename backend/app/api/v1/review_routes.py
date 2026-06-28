from pydantic import BaseModel
from fastapi import APIRouter


router = APIRouter()


class ReviewRequest(BaseModel):
    message_id: str | None = None
    rating: str
    reason_tags: list[str] = []
    comment: str | None = None


@router.post("")
def create_review(req: ReviewRequest) -> dict:
    return {"status": "accepted", "rating": req.rating}
