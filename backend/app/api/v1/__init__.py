from fastapi import APIRouter

from .admin_routes import router as admin_router
from .booking_routes import router as booking_router
from .chat_routes import router as chat_router
from .conversation_routes import router as conversation_router
from .driver_routes import router as driver_router
from .executive_routes import router as executive_router
from .food_routes import router as food_router
from .merchant_routes import router as merchant_router
from .notification_routes import router as notification_router
from .operator_routes import router as operator_router
from .persona_routes import router as persona_router
from .rag_routes import router as rag_router
from .review_routes import router as review_router
from .session_routes import router as session_router
from .voice_routes import router as voice_router

router = APIRouter()
router.include_router(session_router, prefix="/auth", tags=["v1-auth"])
router.include_router(chat_router, prefix="/chat", tags=["v1-chat"])
router.include_router(conversation_router, prefix="/conversations", tags=["v1-conversations"])
router.include_router(persona_router, prefix="/personas", tags=["v1-personas"])
router.include_router(rag_router, prefix="/rag", tags=["v1-rag"])
router.include_router(review_router, prefix="/reviews", tags=["v1-reviews"])
router.include_router(food_router, prefix="/food", tags=["v1-food"])
router.include_router(driver_router, prefix="/driver", tags=["v1-driver"])
router.include_router(merchant_router, prefix="/merchant", tags=["v1-merchant"])
router.include_router(operator_router, prefix="/operator", tags=["v1-operator"])
router.include_router(executive_router, prefix="/executive", tags=["v1-executive"])
router.include_router(booking_router, prefix="/booking", tags=["v1-booking"])
router.include_router(voice_router, prefix="/voice", tags=["v1-voice"])
router.include_router(notification_router, prefix="/notifications", tags=["v1-notifications"])
router.include_router(admin_router, prefix="/admin", tags=["v1-admin"])
