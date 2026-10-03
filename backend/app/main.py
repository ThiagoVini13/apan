"""
APAN API — application factory.

Registers all routers, middleware, and exception handlers.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.modules.classes.router import router as classes_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.roll_calls.router import router as roll_calls_router
from app.modules.students.router import router as students_router
from app.modules.subjects.router import router as subjects_router

API_PREFIX = "/api/v1"

app = FastAPI(
    title="APAN API",
    description="Backend API for the APAN school attendance system",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "detail": exc.detail},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(students_router, prefix=API_PREFIX)
app.include_router(classes_router, prefix=API_PREFIX)
app.include_router(roll_calls_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(subjects_router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Root / health
# ---------------------------------------------------------------------------


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "APAN API is running!"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
