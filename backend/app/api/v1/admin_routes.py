from fastapi import APIRouter, Depends

from app.core.dependency import get_current_admin
from app.schemas.response import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service="xanhsm-backend", version="modular-v1")


@router.get("/me")
def admin_me(admin=Depends(get_current_admin)) -> dict:
    return {"id": admin.id, "email": admin.email, "role": admin.role.value}
