"""
PawCare — Reminders router stub. Trace: FR-09.

Structure only — the real Reminder Service (scheduling, status, dashboard
surfacing) is P2-BE-003 (Phase 2, Sprint Block 9-10).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up. Replaced by
    the real Reminder Service endpoints in P2-BE-003."""
    return {"status": "ok", "router": "reminders"}
