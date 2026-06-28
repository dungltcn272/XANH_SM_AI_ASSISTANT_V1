from fastapi import APIRouter

from app.domains.merchant_copilot.menu_analysis import menu_optimization
from app.domains.merchant_copilot.revenue_analysis import revenue_summary
from app.domains.merchant_copilot.review_analysis import review_sentiment
from app.schemas.response import CapabilityResponse


router = APIRouter()


@router.get("/capabilities", response_model=CapabilityResponse)
def merchant_capabilities() -> CapabilityResponse:
    return CapabilityResponse(
        persona="merchant",
        tools=["merchant_analytics", "menu_analysis", "review_analysis", "promotion_advisor", "menu_ocr"],
        demo_queries=["Doanh thu tuần này thế nào?", "Nên tối ưu menu ra sao?", "Review đang chê gì nhiều nhất?"],
    )


@router.get("/analytics")
def analytics() -> dict:
    return revenue_summary()


@router.get("/menu-optimization")
def menu() -> dict:
    return menu_optimization()


@router.get("/review-sentiment")
def reviews() -> dict:
    return review_sentiment()
