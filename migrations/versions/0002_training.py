"""add training_status columns to daily_summary

Revision ID: 0002_training
Revises: 0001_initial
Create Date: 2026-06-21
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_training"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("daily_summary", sa.Column("training_status", sa.Integer()))
    op.add_column("daily_summary", sa.Column("training_status_phrase", sa.String()))


def downgrade() -> None:
    op.drop_column("daily_summary", "training_status_phrase")
    op.drop_column("daily_summary", "training_status")
