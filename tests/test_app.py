"""Tests for the initial Expense Splitter API endpoints."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_responds_successfully() -> None:
    response = client.get("/")

    assert response.status_code == 200


def test_health_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
