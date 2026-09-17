"""
Phase 0 hello-world backend.

This is deliberately minimal: it exists to prove the container, the API
framework, and (once DATABASE_URL is wired to a running Postgres) the
database connection all work end to end, before any real feature work
starts. See docs/System_Design_and_Requirements.md for the actual API
surface (FR-1..FR-12) that replaces this.
"""
import os

from fastapi import FastAPI

app = FastAPI(
    title="AI-Assisted Cross-Border Tax & Compliance System",
    description="Educational prototype. Not legally binding tax advice.",
    version="0.0.1",
)


@app.get("/health")
def health() -> dict:
    """Liveness check used by Phase 0's hello-world deploy (see PROGRESS.md)."""
    return {
        "status": "ok",
        "service": "backend",
        "database_url_configured": bool(os.environ.get("DATABASE_URL")),
    }


@app.get("/")
def root() -> dict:
    return {
        "message": "AI-Assisted Cross-Border Tax & Compliance System — API is running.",
        "docs": "/docs",
        "health": "/health",
    }
