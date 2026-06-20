import json
import os
import sys

# Ensure we can import app modules when running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import xgboost as xgb
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import FoodInteraction, FoodCatalog
from app.core.logger import log_error, log_warn
from app.food_recommendation.ranking.features import extract_features_from_breakdown
from app.food_recommendation.core.schemas import ScoreBreakdown

MODEL_PATH = "data/models/food_xgboost.json"


def train_xgboost_ranker():
    """
    Huấn luyện mô hình XGBoost để Ranking các món ăn dựa trên lịch sử tương tác.
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    db: Session = SessionLocal()
    try:
        interactions = db.query(FoodInteraction).all()
        
        if len(interactions) < 10:
            log_warn("ML_TRAINING", "Not enough data to train XGBoost. Need at least 10 interactions.")
            return {"success": False, "reason": "Not enough data"}

        X = []
        y = []

        for interaction in interactions:
            if not interaction.request_context_json:
                continue
            try:
                context = json.loads(interaction.request_context_json)
            except json.JSONDecodeError:
                continue
            
            # Label definition
            if interaction.event_type in ("like", "order", "click_item"):
                label = 1
            elif interaction.event_type in ("dislike", "dismiss"):
                label = 0
            else:
                continue  # click_out or unknown
                
            # Trích xuất ScoreBreakdown từ lúc request (nếu có lưu)
            # Vì lúc log chúng ta có lưu breakdown vào request_context không?
            # Hiện tại có thể chưa lưu đầy đủ.
            # Trong thực tế, ta nên reconstruct lại ScoreBreakdown bằng việc gọi ranker
            # Nhưng ở đây để đơn giản ta giả lập features ngẫu nhiên nếu không có sẵn, 
            # hoặc trích xuất từ breakdown_json nếu sau này thêm vào.
            breakdown_dict = context.get("breakdown", {})
            breakdown = ScoreBreakdown(
                recall_score=breakdown_dict.get("recall_score", 0.0),
                nearby_score=breakdown_dict.get("nearby_score", 0.5),
                delivery_fee_score=breakdown_dict.get("delivery_fee_score", 0.5),
                eta_score=breakdown_dict.get("eta_score", 0.5),
                budget_score=breakdown_dict.get("budget_score", 0.5),
                discount_score=breakdown_dict.get("discount_score", 0.0),
                category_score=breakdown_dict.get("category_score", 0.5),
                taste_score=breakdown_dict.get("taste_score", 0.5),
                rating_score=breakdown_dict.get("rating_score", 0.5),
                popularity_score=breakdown_dict.get("popularity_score", 0.5),
                personalization_score=breakdown_dict.get("personalization_score", 0.0),
            )
            features = extract_features_from_breakdown(breakdown)
            
            X.append(features)
            y.append(label)

        if len(X) < 10:
            log_warn("ML_TRAINING", "Not enough valid labeled data to train.")
            return {"success": False, "reason": "Not enough labeled data"}

        model = xgb.XGBClassifier(
            n_estimators=50,
            max_depth=4,
            learning_rate=0.1,
            objective="binary:logistic",
            eval_metric="logloss"
        )
        model.fit(X, y)
        model.save_model(MODEL_PATH)
        return {"success": True, "samples": len(X), "model_path": MODEL_PATH}
        
    except Exception as e:
        log_error("ML_TRAINING", f"Error training XGBoost: {e}")
        return {"success": False, "reason": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    train_xgboost_ranker()
