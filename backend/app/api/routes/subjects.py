from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Subject, term_subjects
from app.schemas.course import SubjectOut

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectOut])
def list_subjects(term_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Subject).order_by(Subject.code)
    if term_id is not None:
        stmt = stmt.join(term_subjects).where(term_subjects.c.term_id == term_id)
    return db.scalars(stmt).all()


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject
