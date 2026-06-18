from __future__ import annotations

import os
from typing import Any
import xgboost as xgb
from app.food_recommendation.schemas import FoodCatalogEntry, FoodRecommendationRequest


class BaseFoodRanker:
    """Khung kiến trúc (Base class) cho mô hình xếp hạng món ăn."""
    def rank(
        self,
        candidates: list[FoodCatalogEntry],
        request: FoodRecommendationRequest,
        candidate_scores: dict[str, float]
    ) -> list[tuple[float, FoodCatalogEntry]]:
        raise NotImplementedError("Phải implement phương thức rank")


class XGBoostFoodRanker(BaseFoodRanker):
    """
    Learning-to-Rank (LTR) với XGBoost.
    Yêu cầu: Lịch sử interaction log (click, order, dismiss).
    Hiện tại: Pass-through (chờ dữ liệu thật).
    """
    def __init__(self, model_path: str = "data/models/food_xgboost.json"):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = xgb.XGBClassifier()
                self.model.load_model(self.model_path)
                self.is_loaded = True
            except Exception as e:
                import logging
                logging.error(f"Failed to load XGBoost model: {e}")
                self.is_loaded = False
                self.model = None

    def predict_scores(self, features_list: list[list[float]]) -> list[float]:
        if not self.is_loaded or not self.model or not features_list:
            return []
        
        # XGBClassifier.predict_proba returns [[prob_0, prob_1], ...]
        # We want the probability of class 1 (positive interaction)
        probs = self.model.predict_proba(features_list)
        return [float(p[1]) for p in probs]



xgb_ranker = XGBoostFoodRanker()

class CohereCrossEncoder(BaseFoodRanker):
    """
    Neural Reranker sử dụng Cohere Rerank API (hoặc BGE Cross-Encoder).
    Dùng để rerank top 50 candidates lấy từ retrieval.
    """
    def __init__(self, api_key: str | None = None, model_name: str = "rerank-multilingual-v3.0"):
        self.api_key = api_key
        self.model_name = model_name

    def rank(
        self,
        candidates: list[FoodCatalogEntry],
        request: FoodRecommendationRequest,
        candidate_scores: dict[str, float]
    ) -> list[tuple[float, FoodCatalogEntry]]:
        # TODO: Khi có nhu cầu rerank thật, gọi API Cohere.
        # Hiện tại: Pass-through.
        return sorted(
            [(candidate_scores.get(c.item_id, 0.0), c) for c in candidates],
            key=lambda x: x[0],
            reverse=True
        )


class TwoTowerRetriever:
    """
    Two-Tower Retrieval sử dụng VectorDB (Qdrant).
    """
    def __init__(self, qdrant_client: Any, collection_name: str = "food_catalog_vectors"):
        self.client = qdrant_client
        self.collection_name = collection_name

    def retrieve(self, user_embedding: list[float], limit: int = 100) -> list[str]:
        # TODO: Query vectorDB để tìm các item_id có khoảng cách gần với user_embedding
        return []


class BanditExplorer:
    """
    Bandit Online Learning (Epsilon-Greedy / Thompson Sampling).
    Đảm bảo tính đa dạng và khám phá (explore) các quán mới.
    """
    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon

    def apply(self, ranked_items: list[tuple[float, FoodCatalogEntry]]) -> list[tuple[float, FoodCatalogEntry]]:
        """
        Trộn lẫn các item mới/chưa được khám phá vào top kết quả.
        """
        if not ranked_items:
            return ranked_items
            
        if random.random() < self.epsilon:
            # Epsilon-Greedy: Chọn ngẫu nhiên một item đẩy lên đầu để lấy data interaction
            idx = random.randint(0, len(ranked_items) - 1)
            explored_item = ranked_items.pop(idx)
            ranked_items.insert(0, explored_item)
            
        return ranked_items
