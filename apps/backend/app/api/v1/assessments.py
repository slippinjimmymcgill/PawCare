"""
PawCare — Symptom assessment router stub. Trace: FR-04, FR-05, FR-06.

Structure only — the real Symptom Assessment Service (NLP -> classifier ->
triage -> response) is P2-BE-001 (Phase 2, Sprint Block 7-8). Nothing in
this router may ever return a diagnosis, prescription, or dosage, per
requirements.md §7's hard constraint — noted here so that constraint is
visible at the exact point future endpoint logic gets added, not just in
a document three folders away.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up. Replaced by
    the real symptom-assessment endpoint in P2-BE-001 — which sits behind
    the Veterinary Safety Layer (P2-RAG-004, FR-08), not in front of it."""
    return {"status": "ok", "router": "assessments"}
