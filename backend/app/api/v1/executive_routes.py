from fastapi import APIRouter

from app.domains.executive_copilot.bi_analysis import bi_summary
from app.domains.executive_copilot.churn_prediction import churn_risk
from app.domains.executive_copilot.expansion_advisor import expansion_advice
from app.domains.executive_copilot.forecast_simulation import voucher_simulation
from app.schemas.response import CapabilityResponse


router = APIRouter()


@router.get("/capabilities", response_model=CapabilityResponse)
def executive_capabilities() -> CapabilityResponse:
    return CapabilityResponse(
        persona="executive",
        tools=["bi_analysis", "forecast_simulation", "churn_prediction", "expansion_advisor"],
        demo_queries=["Tóm tắt BI hôm nay", "Nếu tăng voucher 15% thì đơn tăng bao nhiêu?", "Nên mở rộng thành phố nào?"],
    )


@router.get("/insights")
def insights() -> dict:
    return {"bi": bi_summary(), "voucher_simulation": voucher_simulation(), "churn": churn_risk(), "expansion": expansion_advice()}
