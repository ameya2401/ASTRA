"""
src/api/main.py - FastAPI application entrypoint for AST-Triage.

Configures the FastAPI application instance, manages async lifespan
events (database initialization, model pre-warming), and mounts the
v1 API routers.
"""
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from database.connection import init_db
from src.api.routes import router as api_router
from src.ml_engine.predictor import get_predictor
from src.semantic_engine.drift_analyzer import SemanticDriftAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages FastAPI application startup and shutdown lifecycle.

    Startup:
        1. Initializes async SQLite / PostgreSQL tables.
        2. Pre-warms XGBoost classifier, SHAP explainer, and MiniLM embedder singletons
           to guarantee sub-300ms SLA on all incoming requests.
    Shutdown:
        Cleans up system resources.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")

    # 1. Initialize database schema
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)

    # 2. Pre-warm ML and NLP singletons
    try:
        logger.info("Pre-warming ML and NLP model singletons...")
        get_predictor(model_dir=settings.MODEL_CHECKPOINT_DIR)
        SemanticDriftAnalyzer(model_name=settings.EMBEDDING_MODEL_NAME)
        logger.info("ML and NLP model singletons pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Could not pre-warm all model singletons: {e}")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}.")


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Automated triage and risk stratification for AI-agent-authored pull requests. "
        "Evaluates Tree-sitter AST structural deltas, NLP semantic intent drift, "
        "and test churn using a Platt-calibrated XGBoost model with SHAP explanations."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for web dashboards or developer consoles
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_router)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root metadata endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "triage_url": "/api/v1/triage/analyze",
    }
