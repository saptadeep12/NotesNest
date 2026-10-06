from pydantic import BaseModel, ConfigDict


class TermOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    season: str
    academic_year: str
    is_freshers: bool


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
