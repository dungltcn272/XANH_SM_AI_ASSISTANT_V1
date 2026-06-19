from fastapi import APIRouter, Depends
from app.core.security import get_current_admin

router = APIRouter(dependencies=[Depends(get_current_admin)])

from .knowledge import router as knowledge_router
from .eval import router as eval_router
from .database import router as database_router
from .reviews import router as reviews_router
from .food import router as food_router
from .ml_control import router as ml_router

router.include_router(knowledge_router, tags=["Admin Knowledge"])
router.include_router(eval_router, tags=["Admin Eval"])
router.include_router(database_router, tags=["Admin Database"])
router.include_router(reviews_router, prefix="/reviews", tags=["Admin Reviews"])
router.include_router(food_router, tags=["Admin Food Traces"])
router.include_router(ml_router, prefix="/ml", tags=["Admin ML Control"])
