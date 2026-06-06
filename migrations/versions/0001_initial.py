"""initial schema: metric_samples (hypertable), daily_summary, workouts

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-05
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "metric_samples",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("metric", "ts"),
    )
    # Timescale-specific DDL: Alembic won't autogenerate this, so it's explicit.
    op.execute("SELECT create_hypertable('metric_samples', 'ts')")

    op.create_table(
        "daily_summary",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("resting_hr", sa.Integer()),
        sa.Column("sleep_score", sa.Integer()),
        sa.Column("sleep_duration_s", sa.Integer()),
        sa.Column("total_kilocalories", sa.Integer()),
        sa.Column("active_kilocalories", sa.Integer()),
        sa.Column("bmr_kilocalories", sa.Integer()),
        sa.PrimaryKeyConstraint("day"),
    )

    op.create_table(
        "workouts",
        sa.Column("activity_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("activity_type", sa.String()),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_s", sa.Numeric()),
        sa.Column("distance_m", sa.Numeric()),
        sa.Column("calories", sa.Integer()),
        sa.Column("avg_hr", sa.Integer()),
        sa.Column("max_hr", sa.Integer()),
        sa.PrimaryKeyConstraint("activity_id"),
    )


def downgrade() -> None:
    op.drop_table("workouts")
    op.drop_table("daily_summary")
    op.drop_table("metric_samples")
