from __future__ import annotations

from app.food_recommendation.core.schemas import ScoreBreakdown


def extract_features_from_breakdown(breakdown: ScoreBreakdown) -> list[float]:
    """
    Chuyển đổi ScoreBreakdown thành một mảng số thực (feature vector) để truyền vào XGBoost.
    Thứ tự các feature phải cố định để lúc Train và Predict khớp nhau.
    """
    return [
        breakdown.recall_score,
        breakdown.nearby_score,
        breakdown.delivery_fee_score,
        breakdown.eta_score,
        breakdown.budget_score,
        breakdown.discount_score,
        breakdown.category_score,
        breakdown.taste_score,
        breakdown.rating_score,
        breakdown.popularity_score,
        breakdown.personalization_score,
    ]
