"""Tests for people management endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repository import people_repository


@pytest.fixture(autouse=True)
def reset_people_repository() -> None:
    people_repository.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_add_person(client: TestClient) -> None:
    response = client.post("/api/people", json={"name": "Alice"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Alice"}


def test_list_people(client: TestClient) -> None:
    client.post("/api/people", json={"name": "Alice"})
    client.post("/api/people", json={"name": "Bob"})

    response = client.get("/api/people")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]


def test_person_name_is_trimmed(client: TestClient) -> None:
    response = client.post("/api/people", json={"name": "  Alice  "})

    assert response.status_code == 201
    assert response.json()["name"] == "Alice"


def test_empty_person_name_rejected(client: TestClient) -> None:
    response = client.post("/api/people", json={"name": ""})

    assert response.status_code == 400
    assert response.json() == {"detail": "Person name must not be empty"}


def test_whitespace_only_name_rejected(client: TestClient) -> None:
    response = client.post("/api/people", json={"name": "     "})

    assert response.status_code == 400
    assert response.json() == {"detail": "Person name must not be empty"}


def test_duplicate_person_rejected(client: TestClient) -> None:
    client.post("/api/people", json={"name": "Alice"})

    response = client.post("/api/people", json={"name": "Alice"})

    assert response.status_code == 400
    assert response.json() == {"detail": "A person with this name already exists"}


def test_duplicate_person_case_insensitive(client: TestClient) -> None:
    client.post("/api/people", json={"name": "Alice"})

    response = client.post("/api/people", json={"name": " alice "})

    assert response.status_code == 400


def test_multiple_people_receive_unique_ids(client: TestClient) -> None:
    alice = client.post("/api/people", json={"name": "Alice"}).json()
    bob = client.post("/api/people", json={"name": "Bob"}).json()
    carol = client.post("/api/people", json={"name": "Carol"}).json()

    assert [alice["id"], bob["id"], carol["id"]] == [1, 2, 3]


def test_repository_state_is_isolated_between_tests(client: TestClient) -> None:
    response = client.get("/api/people")

    assert response.json() == []
