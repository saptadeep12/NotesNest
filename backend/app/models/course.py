from sqlalchemy import Boolean, Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Which subjects are offered in which term (managed manually by an admin).
term_subjects = Table(
    "term_subjects",
    Base.metadata,
    Column("term_id", ForeignKey("terms.id", ondelete="CASCADE"), primary_key=True),
    Column("subject_id", ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
)


class Subject(Base):
    """A course, identified by its code. Resources attach here and never change with the term."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))


class Term(Base):
    """An academic term, e.g. "Fall Semester 2026-27" or "Winter Semester 2025-26 Freshers"."""

    __tablename__ = "terms"
    __table_args__ = (UniqueConstraint("season", "academic_year", "is_freshers"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    season: Mapped[str] = mapped_column(String(10))  # "fall" | "winter"
    academic_year: Mapped[str] = mapped_column(String(7))  # "2026-27"
    is_freshers: Mapped[bool] = mapped_column(Boolean, default=False)

    subjects: Mapped[list[Subject]] = relationship(secondary=term_subjects)
