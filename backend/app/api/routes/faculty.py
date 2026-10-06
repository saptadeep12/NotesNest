from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Faculty
from app.schemas.faculty import FacultyOut

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("", response_model=list[FacultyOut])
def list_faculty(db: Session = Depends(get_db)) -> list[Faculty]:
    return db.scalars(select(Faculty).order_by(func.lower(Faculty.name), Faculty.id)).all()
