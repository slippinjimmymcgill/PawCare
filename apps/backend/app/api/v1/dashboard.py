"""
PawCare — Dashboard aggregation router. Trace: FR-10.

Read-only endpoints that assemble the health-monitoring dashboard's four
widgets (weight trend, upcoming reminders, past assessments, record summary)
for a pet, plus a user-level overview for the dashboard's stat strip.

These are projections over data owned by the records/vaccination/medication
modules; the Reminder Service (P2-BE-003) and Assessment Service (P2-BE-001)
will feed the reminder and assessment widgets once they exist.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.pet import Pet
from app.models.user import User
from app.schemas.dashboard import DashboardOverview, DashboardSummary
from app.services.dashboard import build_dashboard_overview, build_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _get_owned_pet_or_404(db: Session, current_user: User, pet_id: str) -> Pet:
    pet = db.scalar(
        select(Pet).where(
            Pet.id == pet_id,
            Pet.user_id == current_user.id,
            Pet.deleted_at.is_(None),
        )
    )
    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found"
        )
    return pet


@router.get("/pets/{pet_id}/summary", response_model=DashboardSummary)
def get_pet_dashboard_summary(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    """All four FR-10 widgets for one pet, with graceful empty states."""
    pet = _get_owned_pet_or_404(db, current_user, pet_id)
    return build_dashboard_summary(db, pet)


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardOverview:
    """User-level roll-up across all non-archived pets."""
    return build_dashboard_overview(db, current_user)


@router.get("/ping")
def ping() -> dict[str, str]:
    """Placeholder route confirming this router is wired up."""
    return {"status": "ok", "router": "dashboard"}
