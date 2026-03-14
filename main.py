"""
AI SkillSync — Main Application Entry Point v2.0.0
====================================================
Production-ready startup with:
  • Centralized config & logging
  • Rate limiting + request tracing middleware
  • Global exception handlers
  • AI model warm-up on startup
  • Health check with system diagnostics
  • All original + 3 new feature routes
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Core infrastructure ───────────────────────────────────────────────────
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.exceptions import register_exception_handlers

# ── Database ──────────────────────────────────────────────────────────────
from app.database.session import engine, Base

# ── Middleware ────────────────────────────────────────────────────────────
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware

# ── Original routes (UNCHANGED — all endpoints preserved) ─────────────────
from app.routes import (
    skill_graph, readiness, skill_gap,
    planner, resume, burnout, simulation, dashboard,
)

# ── New feature routes ────────────────────────────────────────────────────
from app.routes import job_matching, resume_optimizer, career_copilot

# ── AI engine ─────────────────────────────────────────────────────────────
from app.ai.prediction_engine import PredictionEngine

# ---------------------------------------------------------------------------
# Bootstrap logging before anything else runs
# ---------------------------------------------------------------------------
configure_logging()
logger = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("=" * 60)

    # 1. Create all database tables (idempotent)
    logger.info("Initialising database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # 2. Warm up the Digital Twin prediction engine
    logger.info("Training Digital Twin prediction model...")
    prediction_engine = PredictionEngine()
    prediction_engine.train()
    app.state.prediction_engine = prediction_engine
    logger.info("Prediction engine ready.")

    # 3. Store startup time for health check
    app.state.started_at = datetime.now(timezone.utc).isoformat()

    logger.info("%s is ready to serve requests.", settings.APP_NAME)
    logger.info("Docs available at: /docs")

    yield

    # Shutdown
    logger.info("Shutting down %s...", settings.APP_NAME)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered Career Intelligence Platform. "
        "Provides skill graph traversal, career readiness scoring, "
        "adaptive study planning, burnout risk detection, score simulation, "
        "AI job matching, ATS resume optimization, and AI career mentorship."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Exception handlers (must be registered before middleware)
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Middleware stack (applied in reverse order — last added = first executed)
# ---------------------------------------------------------------------------

# 1. CORS — outermost
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate limiter
app.add_middleware(RateLimitMiddleware)

# 3. Request logger — innermost (closest to route handlers)
app.add_middleware(RequestLoggerMiddleware)

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

API_PREFIX = "/api"

# ── Original routes — endpoints UNCHANGED ────────────────────────────────
app.include_router(skill_graph.router,   prefix=API_PREFIX, tags=["Skill Graph"])
app.include_router(readiness.router,     prefix=API_PREFIX, tags=["Career Readiness"])
app.include_router(skill_gap.router,     prefix=API_PREFIX, tags=["Skill Gap"])
app.include_router(planner.router,       prefix=API_PREFIX, tags=["Study Planner"])
app.include_router(resume.router,        prefix=API_PREFIX, tags=["Resume Extractor"])
app.include_router(burnout.router,       prefix=API_PREFIX, tags=["Burnout Risk"])
app.include_router(simulation.router,    prefix=API_PREFIX, tags=["Digital Twin"])
app.include_router(dashboard.router,     prefix=API_PREFIX, tags=["Dashboard"])

# ── New feature routes ────────────────────────────────────────────────────
app.include_router(job_matching.router,     prefix=API_PREFIX, tags=["Job Matching"])
app.include_router(resume_optimizer.router, prefix=API_PREFIX, tags=["Resume Optimizer"])
app.include_router(career_copilot.router,   prefix=API_PREFIX, tags=["Career Copilot"])


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"])
def root():
    """API overview and endpoint directory."""
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "original_endpoints": {
            "skill_graph":   "GET  /api/skill-graph/{career_id}",
            "readiness":     "GET  /api/readiness/{user_id}/{career_id}",
            "skill_gap":     "GET  /api/skill-gap/{user_id}/{career_id}",
            "dashboard":     "GET  /api/dashboard/{user_id}",
            "extract_resume": "POST /api/extract-resume",
            "simulate_score": "POST /api/simulate-score",
            "burnout_risk":  "POST /api/burnout-risk",
            "generate_plan": "POST /api/generate-plan",
        },
        "new_endpoints": {
            "job_matches":      "GET  /api/job-matches/{user_id}",
            "resume_optimize":  "POST /api/resume-optimize",
            "career_copilot":   "POST /api/career-copilot",
        },
    }


# ---------------------------------------------------------------------------
# Health check — production-grade with diagnostics
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    """
    Detailed health check endpoint.
    Returns service status, uptime, database connectivity, and model state.
    """
    from sqlalchemy import text

    db_status = "unknown"
    db_error = None
    try:
        from app.database.session import SessionLocal
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as exc:
        db_status = "unhealthy"
        db_error = str(exc)
        logger.error("Health check — DB error: %s", exc)

    model_ready = getattr(
        getattr(app.state, "prediction_engine", None), "_trained", False
    )

    status = "healthy" if db_status == "healthy" and model_ready else "degraded"

    payload = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "started_at": getattr(app.state, "started_at", None),
        "components": {
            "database": db_status,
            "prediction_model": "ready" if model_ready else "not_ready",
        },
    }

    if db_error:
        payload["components"]["database_error"] = db_error

    return payload
