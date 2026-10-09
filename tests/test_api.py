import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app import main as main_module
from app.main import app
from app.models import Analysis, User


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    app.state.testing_session_factory = TestingSession
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    del app.state.testing_session_factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register(client, email):
    return client.post(
        "/auth/register",
        json={"name": "Test User", "email": email, "password": "strong-pass-123"},
    )


def login(client, email):
    response = client.post("/auth/login", json={"email": email, "password": "strong-pass-123"})
    return response.json()["access_token"]


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_hashes_password_and_does_not_return_hash(client):
    response = register(client, "alice@example.com")
    assert response.status_code == 201
    assert "hashed_password" not in response.json()


def test_duplicate_email_returns_conflict(client):
    assert register(client, "alice@example.com").status_code == 201
    assert register(client, "alice@example.com").status_code == 409


def test_registration_rejects_passwords_over_bcrypt_byte_limit(client):
    response = client.post(
        "/auth/register",
        json={"name": "Test User", "email": "alice@example.com", "password": "x" * 73},
    )
    assert response.status_code == 422
    assert "72 UTF-8 bytes" in response.text


def test_login_returns_bearer_token(client):
    register(client, "alice@example.com")
    response = client.post("/auth/login", json={"email": "alice@example.com", "password": "strong-pass-123"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_bad_password_returns_unauthorized(client):
    register(client, "alice@example.com")
    response = client.post("/auth/login", json={"email": "alice@example.com", "password": "not-the-password"})
    assert response.status_code == 401


def test_protected_history_rejects_missing_token(client):
    response = client.get("/analyses")
    assert response.status_code == 401


def test_analyze_rejects_empty_description_and_non_pdf(client):
    register(client, "alice@example.com")
    token = login(client, "alice@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    empty_description = client.post(
        "/analyze",
        headers=headers,
        data={"job_description": " "},
        files={"resume": ("resume.pdf", b"%PDF-test", "application/pdf")},
    )
    assert empty_description.status_code == 400
    non_pdf = client.post(
        "/analyze",
        headers=headers,
        data={"job_description": "Python engineer"},
        files={"resume": ("resume.txt", b"plain text", "text/plain")},
    )
    assert non_pdf.status_code == 400


def test_analyze_rejects_files_that_reach_the_size_limit(client):
    register(client, "alice@example.com")
    token = login(client, "alice@example.com")
    response = client.post(
        "/analyze",
        headers={"Authorization": f"Bearer {token}"},
        data={"job_description": "Python engineer"},
        files={"resume": ("resume.pdf", b"%PDF-" + b"x" * (5 * 1024 * 1024 - 5), "application/pdf")},
    )
    assert response.status_code == 400
    assert "5 MB" in response.json()["detail"]


def test_analyze_persists_results_and_tracks_improvement(client, monkeypatch):
    register(client, "alice@example.com")
    token = login(client, "alice@example.com")
    resume_texts = iter(
        [
            "Experienced Python backend developer building REST API services with PostgreSQL. "
            "Delivered 20 projects and improved response time by 30 percent.",
            "Experienced Python backend developer building REST API services with PostgreSQL, "
            "Docker, and Kubernetes. Delivered 20 projects and improved response time by 30 percent.",
        ]
    )
    monkeypatch.setattr(main_module, "extract_text", lambda _: next(resume_texts))
    headers = {"Authorization": f"Bearer {token}"}
    job = "Python backend developer required. Experience with REST API services, PostgreSQL, Docker, and Kubernetes."

    first = client.post(
        "/analyze",
        headers=headers,
        data={"job_title": "Backend Engineer", "job_description": job},
        files={"resume": ("resume.pdf", b"%PDF-first", "application/pdf")},
    )
    assert first.status_code == 201
    first_result = first.json()
    assert "docker" in first_result["missing_skills"]

    second = client.post(
        "/analyze",
        headers=headers,
        data={
            "job_title": "Backend Engineer",
            "job_description": job,
            "compare_with": str(first_result["id"]),
        },
        files={"resume": ("improved.pdf", b"%PDF-second", "application/pdf")},
    )
    assert second.status_code == 201
    second_result = second.json()
    assert second_result["comparison"]["previous_score"] == first_result["score"]
    assert second_result["comparison"]["score_change"] > 0
    assert {"docker", "kubernetes"} <= set(second_result["comparison"]["newly_matched_skills"])
    assert client.get("/analyses", headers=headers).status_code == 200
    detail = client.get(f"/analyses/{first_result['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["job_description"] == job
    assert "Python backend developer" in detail.json()["resume_text"]
    assert client.delete(f"/analyses/{first_result['id']}", headers=headers).status_code == 204


def test_users_cannot_read_another_users_analysis(client):
    register(client, "alice@example.com")
    register(client, "bob@example.com")
    token_a = login(client, "alice@example.com")
    token_b = login(client, "bob@example.com")
    db = app.state.testing_session_factory()
    user_a = db.query(User).filter_by(email="alice@example.com").one()
    db.add(
        Analysis(
            user_id=user_a.id,
            job_title="Private role",
            resume_text="Resume",
            job_description="Description",
            score=50,
            skill_match=50,
            text_similarity=50,
            matched_skills=json.dumps(["python"]),
            missing_skills=json.dumps([]),
            suggestions=json.dumps([]),
        )
    )
    db.commit()
    db.close()
    assert client.get("/analyses", headers={"Authorization": f"Bearer {token_a}"}).status_code == 200
    assert client.get("/analyses/1", headers={"Authorization": f"Bearer {token_b}"}).status_code == 404
