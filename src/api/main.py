"""
Day 38 - FastAPI application for Nifty100 Financial Intelligence.
"""

import logging
import sqlite3
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import DB_PATH
from src.api.routers import (
    companies,
    documents,
    financials,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

# ---------------------------------------------------------
# Application configuration
# ---------------------------------------------------------

APP_VERSION = "1.0.0"

START_TIME = time.time()


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("nifty100_api")


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Nifty100 Financial Intelligence API",
    description="REST API for Nifty100 financial intelligence data.",
    version=APP_VERSION,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------

app.include_router(
    companies.router,
    prefix="/api/v1",
)
app.include_router(
    financials.router,
    prefix="/api/v1",
)
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(
    peers.router,
    prefix="/api/v1",
)
app.include_router(
    valuation.router,
    prefix="/api/v1",
)

app.include_router(
    portfolio.router,
    prefix="/api/v1",
)
app.include_router(
    documents.router,
    prefix="/api/v1",
)
# ---------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------


@app.middleware("http")
async def log_requests(request, call_next):
    """Log API requests and response status."""

    start = time.time()

    response = await call_next(request)

    duration = time.time() - start

    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------


@app.get("/api/v1/health")
def health():
    """Return API and database health information."""

    table_names = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "sectors",
        "peer_groups",
        "peer_percentiles",
        "market_cap",
        "analysis",
    ]

    db_row_counts = {}

    try:
        conn = sqlite3.connect(DB_PATH)

        for table in table_names:

            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")

            db_row_counts[table] = cursor.fetchone()[0]

        conn.close()

        database_status = "ok"

    except Exception as exc:

        logger.exception("Database health check failed")

        database_status = "error"

        return {
            "status": "error",
            "database_status": database_status,
            "db_row_counts": db_row_counts,
            "uptime_seconds": round(
                time.time() - START_TIME,
                2,
            ),
            "version": APP_VERSION,
            "error": str(exc),
        }

    return {
        "status": "ok",
        "database_status": database_status,
        "db_row_counts": db_row_counts,
        "uptime_seconds": round(
            time.time() - START_TIME,
            2,
        ),
        "version": APP_VERSION,
    }


# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------


@app.get("/")
def root():
    """Return basic API information."""

    return {
        "name": "Nifty100 Financial Intelligence API",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
