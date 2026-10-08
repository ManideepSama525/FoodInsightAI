"""phase19 durable jobs

Revision ID: 0003_phase19_jobs
Revises: 0002_phase11_persistence
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_phase19_jobs"
down_revision = "0002_phase11_persistence"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "job_records",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("kind", sa.String(length=80), nullable=False),
        sa.Column("subject_id", sa.String(length=64), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True, unique=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_records_kind", "job_records", ["kind"])
    op.create_index("ix_job_records_subject_id", "job_records", ["subject_id"])
    op.create_index("ix_job_records_status", "job_records", ["status"])

def downgrade():
    op.drop_index("ix_job_records_status", table_name="job_records")
    op.drop_index("ix_job_records_subject_id", table_name="job_records")
    op.drop_index("ix_job_records_kind", table_name="job_records")
    op.drop_table("job_records")
