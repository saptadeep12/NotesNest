def test_terms_exclude_summer_and_newest_first(client):
    terms = client.get("/api/v1/terms").json()
    assert terms
    assert all("Summer" not in t["name"] for t in terms)
    assert terms[0]["academic_year"] == "2025-26"


def test_subjects_filtered_by_term(client):
    terms = client.get("/api/v1/terms").json()
    current = next(t for t in terms if t["name"] == "Fall Semester 2025-26 Freshers")
    assert len(client.get(f"/api/v1/subjects?term_id={current['id']}").json()) == 6
    assert client.get("/api/v1/subjects?term_id=9999").json() == []


def test_subject_by_id_and_missing_subject(client):
    subject = client.get("/api/v1/subjects").json()[0]
    assert client.get(f"/api/v1/subjects/{subject['id']}").json() == subject
    assert client.get("/api/v1/subjects/9999").status_code == 404
