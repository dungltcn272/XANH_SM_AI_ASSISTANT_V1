from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.config.settings import settings
from app.core.exceptions import install_exception_handlers
from app.core.logging.request_log import log_request
from app.core.middleware import attach_request_id, install_cors
from app.assistant.nlu.intent_classifier import warmup_nlu
from app.integrations.openai_client import warmup_embeddings
from app.schemas.response import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    warmup_nlu()
    warmup_embeddings()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Modular AI Assistant Platform API for Xanh SM/Vin personas.",
        version="1.0.0",
        lifespan=lifespan,
    )
    install_cors(app)
    install_exception_handlers(app)
    app.middleware("http")(attach_request_id)
    app.middleware("http")(log_request)
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(service="xanhsm-backend", version="modular-v1")
