"""
PawCare — Auth router stub. Trace: FR-01.

Structure only, per P1-BE-001's scope — real registration/login/JWT/
password-reset logic is P1-BE-003 (Sprint Block 3-4). This file exists now
so the route tree and import path are fixed before that task starts.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up. Replaced by
    real endpoints (register/login/logout/password-reset) in P1-BE-003."""
    return {"status": "ok", "router": "auth"}
