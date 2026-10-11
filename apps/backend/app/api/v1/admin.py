"""
PawCare — Admin router stub. Trace: FR-12.

Structure only — real user/knowledge-base-document management endpoints
are P2-BE-005 (Phase 2, Sprint Block 9-10). These routes will need
role-based access control (admin only) once real logic lands — flagged
here, not yet enforced, since there's no auth system in front of it yet.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up. Replaced by
    real admin endpoints (RBAC-gated) in P2-BE-005."""
    return {"status": "ok", "router": "admin"}
