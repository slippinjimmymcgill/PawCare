"""
PawCare — User Pydantic schemas (API request/response shapes).
Trace: FR-01, requirements.md §5.

Placeholder only, per P1-BE-001's scope — real field sets (UserCreate,
UserRead, UserLogin, Token, etc.) land with P1-BE-003 (Auth service),
matching whatever `app.models.User` (P1-BE-002) actually defines. Not
pre-written here so this doesn't drift from that model before it exists.
"""

from pydantic import BaseModel


class UserBase(BaseModel):
    """Placeholder — fields added in P1-BE-003 alongside the real auth
    endpoints (email, name, role; never password_hash)."""
