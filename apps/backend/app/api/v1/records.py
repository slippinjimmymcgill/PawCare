"""
PawCare — Health records router stub. Trace: FR-03.

Structure only — real CRUD (vaccinations, medications, visits, weight
logs, attachments) is P1-BE-005 / P1-BE-006 (Sprint Block 3-4).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up. Replaced by
    real health-record CRUD endpoints in P1-BE-005/P1-BE-006."""
    return {"status": "ok", "router": "records"}
