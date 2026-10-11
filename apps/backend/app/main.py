"""
PawCare backend — FastAPI entrypoint.

Task: P1-BE-001 · Depends on: P0-BE-001, P0-OPS-003 · Trace: plan.md §2

Run locally with:
    uvicorn app.main:app --reload --port 8000

This task is structure only (see docs/design/wireframes and
task_backlog.md P1-BE-001's "Do NOT" clause) — no real endpoint logic
lives here or in app/api/v1/*.py yet. That lands with each feature's own
task (P1-BE-003 onward).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="PawCare API",
    description=(
        "AI-powered pet-health assistant — decision support and "
        "education only. Never a diagnosis, prescription, or "
        "replacement for a veterinarian. See requirements.md §7."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Root health check, per P1-BE-001's acceptance gate. Does not check
    database/LLM connectivity — this is a liveness probe for the API
    process itself, not a readiness probe for its dependencies. A real
    readiness check (DB ping, etc.) is a P1-BE-002/P1-OPS-001 concern,
    once there's a real database to ping."""
    return {"status": "ok"}
