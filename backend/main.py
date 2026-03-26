"""
MentorOS – FastAPI Application Entry Point
Production-grade: CORS, rate limiting, structured logging, health checks.
"""
import os
import sys
import logging

# Ensure the backend directory is importable on Vercel and locally
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.database import init_db, ensure_db, mongodb
from routes.auth import router as auth_router
from routes.tasks import router as tasks_router
from routes.notes import router as notes_router
from routes.roadmaps import router as roadmaps_router
from routes.extras import (
    res_router, plan_router, review_router,
    teacher_router, analytics_router, reminder_router,
)

# ── Structured logging ────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
        if not settings.is_production
        else structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()
logging.basicConfig(level=logging.INFO)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown hooks.
    Never raises — startup failures are logged and gracefully degraded.
    """
    log.info("mentoross.starting", version=settings.APP_VERSION, env=settings.ENVIRONMENT)
    settings.warn_if_insecure()
    await init_db()
    log.info("mentoross.ready", db_ready=mongodb.ready)
    yield
    log.info("mentoross.shutdown")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Personal Learning OS — Production API",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────────────
# IMPORTANT: This middleware MUST catch all exceptions internally.
# If an exception propagates out of call_next() it bypasses FastAPI's
# exception handlers and crashes the Starlette task group → raw 500 traceback.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start = time.time()
    # Lazy reconnect: if a warm instance has a stale failed connection,
    # attempt to reconnect before serving the request
    if not mongodb.ready:
        await ensure_db()
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)
        log.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start) * 1000, 2)
        # Detect DB-not-initialised errors specifically
        exc_name = type(exc).__name__
        if "CollectionWasNotInitialized" in exc_name or "not initialized" in str(exc).lower():
            log.warning(
                "http.db_not_ready",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            return JSONResponse(
                status_code=503,
                content={
                    "detail": (
                        "The database is not connected. "
                        "Please set MONGODB_URI, SECRET_KEY, and ENVIRONMENT "
                        "in Vercel → Settings → Environment Variables, then redeploy."
                    )
                },
            )
        log.error(
            "http.unhandled_exception",
            method=request.method,
            path=request.url.path,
            error=str(exc),
            duration_ms=duration_ms,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again."},
        )


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    exc_name = type(exc).__name__
    if "CollectionWasNotInitialized" in exc_name:
        log.warning("db.not_initialized", path=request.url.path)
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "Database not connected. "
                    "Set MONGODB_URI in Vercel → Settings → Environment Variables."
                )
            },
        )
    log.error("unhandled.exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(notes_router)
app.include_router(roadmaps_router)
app.include_router(res_router, prefix="/resources")
app.include_router(plan_router, prefix="/plans")
app.include_router(plan_router, prefix="/planner")
app.include_router(review_router, prefix="/reviewer")
app.include_router(teacher_router, prefix="/teacher")
app.include_router(analytics_router, prefix="/analytics")
app.include_router(reminder_router, prefix="/reminders")


# ── Health / Info ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "healthy" if mongodb.ready else "degraded",
        "db": "connected" if mongodb.ready else "unavailable — set MONGODB_URI in Vercel env vars",
        "version": settings.APP_VERSION,
        "env": settings.ENVIRONMENT,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ok",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=not settings.is_production,
        log_level="info",
    )
