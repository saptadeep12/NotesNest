from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Term
from app.schemas.course import TermOut

router = APIRouter(prefix="/terms", tags=["terms"])


@router.get("", response_model=list[TermOut])
def list_terms(db: Session = Depends(get_db)):
    stmt = select(Term).order_by(
        Term.academic_year.desc(), Term.season.asc(), Term.is_freshers.asc()
    )
    return db.scalars(stmt).all()


@router.get("/{term_id}", response_model=TermOut)
def get_term(term_id: int, db: Session = Depends(get_db)):
    term = db.get(Term, term_id)
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    return term
