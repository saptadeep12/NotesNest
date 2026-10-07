from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Resource
from app.models.enums import ResourceType
from app.schemas.resource import ResourceOut
from app.services.storage import get_file_response, resolve_path

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[ResourceOut])
def list_resources(
    subject_id: int, type: ResourceType | None = None, db: Session = Depends(get_db)
):
    stmt = select(Resource).where(Resource.subject_id == subject_id)
    if type is not None:
        stmt = stmt.where(Resource.type == type)
        if type == ResourceType.pyq:
            stmt = stmt.order_by(Resource.year.desc().nulls_last(), Resource.exam, Resource.title)
        else:
            stmt = stmt.order_by(Resource.title)
    else:
        stmt = stmt.order_by(
            case((Resource.type == ResourceType.pyq, 0), else_=1),
            Resource.year.desc().nulls_last(),
            Resource.exam,
            Resource.title,
        )
    return db.scalars(stmt).all()


@router.get("/{resource_id}/file")
def get_resource_file(resource_id: int, download: int = 0, db: Session = Depends(get_db)):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    try:
        return get_file_response(
            resource.file_path,
            download=bool(download),
            resolver=resolve_path,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc
