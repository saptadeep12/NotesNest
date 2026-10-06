from pydantic import BaseModel, ConfigDict


class FacultyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    designation: str | None
    department: str | None
    email: str | None
    cabin: str | None
