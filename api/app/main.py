"""COREcare v2 API — FastAPI application factory."""

import time
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.billing import router as billing_router
from app.routers.caregivers import router as caregivers_router
from app.routers.charts import router as charts_router
from app.routers.clients import router as clients_router
from app.routers.credentials import router as credentials_router
from app.routers.notifications import router as notifications_router
from app.routers.payroll import router as payroll_router
from app.routers.shifts import router as shifts_router
from app.routers.users import router as users_router

logger = structlog.get_logger()


def setup_logging() -> None:
    """Configure structlog for structured JSON logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if settings.debug
            else structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="COREcare v2 API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable[..., Any]) -> Response:
        start = time.monotonic()
        response: Response = await call_next(request)
        elapsed = time.monotonic() - start
        await logger.ainfo(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed * 1000, 2),
        )
        return response

    app.include_router(users_router)
    app.include_router(clients_router)
    app.include_router(caregivers_router)
    app.include_router(shifts_router)
    app.include_router(charts_router)
    app.include_router(credentials_router)
    app.include_router(payroll_router)
    app.include_router(billing_router)
    app.include_router(notifications_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
