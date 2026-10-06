"""Add notification preferences.

Revision ID: 0002_notification_preferences
Revises: 0001_initial_schema
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_notification_preferences"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("min_fit_score", sa.Integer(), nullable=False, server_default="80"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
