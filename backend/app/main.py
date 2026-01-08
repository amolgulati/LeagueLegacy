"""
Fantasy League History Tracker - FastAPI Backend

This API provides endpoints for tracking fantasy league history
across Yahoo Fantasy and Sleeper platforms.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.api.sleeper import router as sleeper_router
from app.api.yahoo import router as yahoo_router
from app.api.owners import router as owners_router
from app.api.history import router as history_router
from app.api.trades import router as trades_router
from app.api.records import router as records_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Fantasy League History Tracker",
    description="Unified fantasy league history tracking for Yahoo Fantasy and Sleeper",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint returning API info."""
    return {
        "name": "Fantasy League History Tracker API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(sleeper_router)
app.include_router(yahoo_router)
app.include_router(owners_router)
app.include_router(history_router)
app.include_router(trades_router)
app.include_router(records_router)
