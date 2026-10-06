from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Article
from app.schemas.article import ArticleListOut, ArticleOut

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[ArticleListOut])
def list_articles(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Article]:
    statement = select(Article).order_by(Article.order, Article.title)
    if category is not None:
        statement = statement.where(func.lower(Article.category) == category.lower())
    return db.scalars(statement).all()


@router.get("/{slug}", response_model=ArticleOut)
def get_article(slug: str, db: Session = Depends(get_db)) -> Article:
    article = db.scalar(select(Article).where(Article.slug == slug))
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
