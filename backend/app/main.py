"""
PayGuard AI — FastAPI Application Entry Point
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.schemas import HealthResponse
from app.api.analyze import router as analyze_router
from app.api.paypal import router as paypal_router
from app.api.transactions import router as transactions_router

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("payguard")
settings = get_settings()

# ──────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup."""
    logger.info("PayGuard AI starting up...")
    logger.info("Environment: %s", settings.app_env)
    logger.info("LLM Provider: %s (available=%s)", settings.llm_provider, settings.llm_available)
    logger.info("PayPal configured: %s", settings.paypal_configured)
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("PayGuard AI shutting down.")


# ──────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="PayGuard AI",
    description=(
        "AI-Powered Payment Risk & Scam Shield. "
        "Analyzes payment context for risk signals before you send money."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(paypal_router, prefix="/api", tags=["PayPal"])
app.include_router(transactions_router, prefix="/api", tags=["Transactions"])


# ── Health Check ────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """Backend health and configuration status."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        llm_available=settings.llm_available,
        llm_provider=settings.llm_provider,
        paypal_configured=settings.paypal_configured,
        database="sqlite",
    )


# ── Root ────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "PayGuard AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
