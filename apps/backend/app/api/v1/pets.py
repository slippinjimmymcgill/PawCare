"""
PawCare — Pets router stub. Trace: FR-02.

Structure only — real CRUD is P1-BE-004 (Sprint Block 3-4).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up. Replaced by
    real pet-profile CRUD endpoints in P1-BE-004."""
    return {"status": "ok", "router": "pets"}
