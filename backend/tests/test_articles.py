from datetime import UTC, datetime

from app.manage import parse_article_file, sync_advice
from app.models import Article


def write_article(path, *, title="First article", category="Exams", order=1):
    path.write_text(
        f"""---
title: {title}
category: {category}
summary: A useful summary
order: {order}
---
# Heading

Article body.
"""
    )


def test_frontmatter_parsing_and_slug_validation(tmp_path):
    path = tmp_path / "good-article.md"
    write_article(path)
    slug, frontmatter, body, _ = parse_article_file(path)
    assert slug == "good-article"
    assert frontmatter.title == "First article"
    assert "# Heading" in body

    bad_slug = tmp_path / "Bad Article.md"
    write_article(bad_slug)
    try:
        parse_article_file(bad_slug)
    except ValueError as exc:
        assert "Bad Article.md" in str(exc)
        assert "kebab-case" in str(exc)
    else:
        raise AssertionError("Invalid slug was accepted")


def test_missing_required_frontmatter_names_file(tmp_path):
    path = tmp_path / "missing-summary.md"
    path.write_text("---\ntitle: Missing summary\ncategory: Exams\n---\nBody")
    try:
        parse_article_file(path)
    except ValueError as exc:
        assert "missing-summary.md" in str(exc)
        assert "summary" in str(exc)
    else:
        raise AssertionError("Missing required field was accepted")


def test_sync_advice_is_idempotent_updates_and_removes(session_factory, tmp_path):
    advice_dir = tmp_path / "advice"
    advice_dir.mkdir()
    first = advice_dir / "first-article.md"
    second = advice_dir / "second-article.md"
    write_article(first, order=2)
    write_article(second, title="Second article", order=3)
    with session_factory() as db:
        assert sync_advice(db, advice_dir) == {"added": 2, "updated": 0, "removed": 0}
        assert sync_advice(db, advice_dir) == {"added": 0, "updated": 0, "removed": 0}
        write_article(first, title="Edited article", order=1)
        second.unlink()
        assert sync_advice(db, advice_dir) == {"added": 0, "updated": 1, "removed": 1}
        article = db.query(Article).one()
        assert article.title == "Edited article"


def test_article_routes_order_filter_and_missing_detail(client, session_factory):
    with session_factory() as db:
        db.add_all(
            [
                Article(
                    slug="z-article",
                    title="Z article",
                    category="Career",
                    summary="Z",
                    body="Z body",
                    order=2,
                    updated_at=datetime.now(UTC).replace(tzinfo=None),
                ),
                Article(
                    slug="a-article",
                    title="A article",
                    category="Exams",
                    summary="A",
                    body="A body",
                    order=1,
                    updated_at=datetime.now(UTC).replace(tzinfo=None),
                ),
            ]
        )
        db.commit()
    response = client.get("/api/v1/articles")
    assert [article["slug"] for article in response.json()] == ["a-article", "z-article"]
    assert "body" not in response.json()[0]
    filtered = client.get("/api/v1/articles?category=exams").json()
    assert [article["slug"] for article in filtered] == ["a-article"]
    assert client.get("/api/v1/articles/a-article").json()["body"] == "A body"
    assert client.get("/api/v1/articles/nope").status_code == 404
