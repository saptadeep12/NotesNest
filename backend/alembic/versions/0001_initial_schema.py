"""initial simplified schema"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"], unique=True)
    op.create_table(
        "terms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("season", sa.String(length=10), nullable=False),
        sa.Column("academic_year", sa.String(length=7), nullable=False),
        sa.Column("is_freshers", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("season", "academic_year", "is_freshers"),
    )
    op.create_table(
        "term_subjects",
        sa.Column("term_id", sa.Integer(), sa.ForeignKey("terms.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("type", sa.Enum("pyq", "note", name="resourcetype", native_enum=False, length=10), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False, unique=True),
        sa.Column("exam", sa.String(length=20)),
        sa.Column("year", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resources_subject_id", "resources", ["subject_id"])


def downgrade() -> None:
    op.drop_index("ix_resources_subject_id", table_name="resources")
    op.drop_table("resources")
    op.drop_table("term_subjects")
    op.drop_table("terms")
    op.drop_index("ix_subjects_code", table_name="subjects")
    op.drop_table("subjects")
