from pydantic import BaseModel, ConfigDict

from app.models.enums import ResourceType


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    type: ResourceType
    title: str
    exam: str | None
    year: int | None
