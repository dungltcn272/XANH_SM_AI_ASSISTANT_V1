import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import FoodInteraction
from app.scripts.train_food_ranker import train_xgboost_ranker

router = APIRouter()

MODEL_PATH = "data/models/food_xgboost.json"

@router.get("/status")
def get_ml_status(
    db: Session = Depends(get_db),
):
    interaction_count = db.query(FoodInteraction).count()
    is_model_loaded = os.path.exists(MODEL_PATH)
    
    return {
        "interaction_count": interaction_count,
        "is_model_loaded": is_model_loaded,
        "model_path": MODEL_PATH if is_model_loaded else None,
        "active_ranker": "XGBoost (AI-based)" if is_model_loaded else "Rule-based (Heuristic)"
    }


def background_train_task():
    try:
        from app.food_recommendation.ml_ranker import xgb_ranker
        train_xgboost_ranker()
        xgb_ranker.load_model()
    except Exception as e:
        import logging
        logging.error(f"Background training failed: {e}")

@router.post("/train")
def trigger_ml_training(
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(background_train_task)
    return {"success": True, "message": "Quá trình huấn luyện đã được bắt đầu ở chế độ nền. Vui lòng kiểm tra lại trạng thái sau ít phút."}
