"""baseline_migration

Revision ID: 8dc0a941e766
Revises:
Create Date: 2026-10-11 20:51:43.102416
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8dc0a941e766"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "migration_probe",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("migration_probe")
