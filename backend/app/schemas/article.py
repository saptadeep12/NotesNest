from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    category: str
    summary: str
    author: str | None
    order: int
    updated_at: datetime


class ArticleOut(ArticleListOut):
    body: str
