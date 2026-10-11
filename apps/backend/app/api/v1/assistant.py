"""
PawCare — AI assistant router stub. Trace: FR-07.

Structure only — the real RAG-grounded chat endpoint (session/message
persistence, source citations) is P2-BE-002 (Phase 2, Sprint Block 7-8).
Like assessments.py, this sits behind the Veterinary Safety Layer
(P2-RAG-004, FR-08) once that's built — not a detail to add later as an
afterthought.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up. Replaced by
    the real assistant chat endpoint in P2-BE-002."""
    return {"status": "ok", "router": "assistant"}
