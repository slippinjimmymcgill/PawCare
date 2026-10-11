"""
PawCare — User model. Trace: FR-01, requirements.md §5.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPKMixin
from .enums import UserRole

if TYPE_CHECKING:
    from .feedback import Feedback
    from .pet import Pet


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.OWNER, nullable=False
    )

    # P1-BE-003 (Auth service) is where login/registration logic lives;
    # this model only holds the data shape.
    pets: Mapped[list["Pet"]] = relationship(back_populates="owner")
    feedback_entries: Mapped[list["Feedback"]] = relationship(back_populates="user")
