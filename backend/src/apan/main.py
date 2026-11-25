"""APAN API application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apan.core.cache import create_redis
from apan.core.config import Settings, get_settings
from apan.core.constants import API_PREFIX, REQUEST_ID_HEADER
from apan.core.database import Database
from apan.core.error_handlers import register_error_handlers
from apan.core.logging import configure_logging
from apan.core.middleware import RequestContextMiddleware
from apan.modules.classes.router import router as classes_router
from apan.modules.dashboard.router import router as dashboard_router
from apan.modules.health.router import router as health_router
from apan.modules.roll_calls.router import router as roll_calls_router
from apan.modules.students.router import router as students_router
from apan.modules.subjects.router import router as subjects_router


def _api_router() -> APIRouter:
    api = APIRouter(prefix=API_PREFIX)
    api.include_router(health_router)
    api.include_router(students_router)
    api.include_router(classes_router)
    api.include_router(roll_calls_router)
    api.include_router(dashboard_router)
    api.include_router(subjects_router)
    return api


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    database = Database(settings)
    redis = create_redis(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await redis.aclose()
            await database.dispose()

    app = FastAPI(
        title="APAN API",
        description="Backend API for the APAN school attendance system",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.database = database
    app.state.redis = redis

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)

    app.include_router(_api_router())
    return app
