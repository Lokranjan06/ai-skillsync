"""
AI SkillSync — Main Application Entry Point
============================================
Bootstraps the FastAPI app, registers all routers, configures CORS,
initialises the database, and warms up the AI prediction engine.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.session import engine, Base
from app.routes import skill_graph, readiness, skill_gap, planner, resume, burnout, simulation, dashboard
from app.ai.prediction_engine import PredictionEngine


# ---------------------------------------------------------------------------
# Lifespan — runs once on startup and once on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all database tables (no-op if they already exist)
    Base.metadata.create_all(bind=engine)

    # 2. Warm-up: pre-train the Digital Twin regression model so the first
    #    request is not slow.
    app.state.prediction_engine = PredictionEngine()
    app.state.prediction_engine.train()

    yield
    # (shutdown logic goes here if needed)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI SkillSync",
    description=(
        "An AI-powered Learning & Career Intelligence System. "
        "Provides skill graph traversal, career readiness scoring, "
        "adaptive study planning, burnout risk detection, and score simulation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Allow all origins in development; tighten in production via environment vars.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

API_PREFIX = "/api"

app.include_router(skill_graph.router,  prefix=API_PREFIX, tags=["Skill Graph"])
app.include_router(readiness.router,    prefix=API_PREFIX, tags=["Career Readiness"])
app.include_router(skill_gap.router,    prefix=API_PREFIX, tags=["Skill Gap"])
app.include_router(planner.router,      prefix=API_PREFIX, tags=["Study Planner"])
app.include_router(resume.router,       prefix=API_PREFIX, tags=["Resume Extractor"])
app.include_router(burnout.router,      prefix=API_PREFIX, tags=["Burnout Risk"])
app.include_router(simulation.router,   prefix=API_PREFIX, tags=["Digital Twin"])
app.include_router(dashboard.router,    prefix=API_PREFIX, tags=["Dashboard"])


@app.get("/", tags=["Root"])
def root():
    """Root endpoint with API information."""
    return {
        "status": "online",
        "message": "AI SkillSync API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "burnout": "POST /api/burnout-risk",
            "simulation": "POST /api/simulate-score",
            "resume": "POST /api/extract-resume",
            "planner": "POST /api/generate-plan",
            "readiness": "GET /api/readiness/{user_id}/{career_id}",
            "skill_gap": "GET /api/skill-gap/{user_id}/{career_id}",
            "skill_graph": "GET /api/skill-graph/{career_id}",
            "dashboard": "GET /api/dashboard/{user_id}"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check endpoint."""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI SkillSync"
    }
