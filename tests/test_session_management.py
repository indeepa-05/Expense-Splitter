"""Tests for safe person deletion and full in-memory session reset."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repository import expense_repository, people_repository


@pytest.fixture(autouse=True)
def reset_repositories() -> Iterator[None]:
    people_repository.reset()
    expense_repository.reset()
    yield
    people_repository.reset()
    expense_repository.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def add_person(client: TestClient, name: str) -> dict[str, object]:
    return client.post("/api/people", json={"name": name}).json()


def equal_expense(
    payer_id: int,
    participant_ids: list[int],
    amount: str = "100.00",
) -> dict[str, object]:
    return {
        "description": "Test expense",
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "equal",
        "participant_ids": participant_ids,
    }


def test_delete_unreferenced_person(client: TestClient) -> None:
    alice = add_person(client, "Alice")

    response = client.delete(f"/api/people/{alice['id']}")

    assert response.status_code == 204
    assert client.get("/api/people").json() == []


def test_delete_missing_person_returns_404(client: TestClient) -> None:
    response = client.delete("/api/people/99")

    assert response.status_code == 404
    assert response.json() == {"detail": "Person 99 does not exist"}


def test_delete_person_used_as_payer_is_rejected(client: TestClient) -> None:
    alice = add_person(client, "Alice")
    bob = add_person(client, "Bob")
    client.post(
        "/api/expenses",
        json=equal_expense(int(alice["id"]), [int(bob["id"])]),
    )

    response = client.delete(f"/api/people/{alice['id']}")

    assert response.status_code == 409
    assert "used in existing expenses" in response.json()["detail"]


def test_delete_person_used_as_equal_participant_is_rejected(
    client: TestClient,
) -> None:
    alice = add_person(client, "Alice")
    bob = add_person(client, "Bob")
    client.post(
        "/api/expenses",
        json=equal_expense(int(alice["id"]), [int(bob["id"])]),
    )

    assert client.delete(f"/api/people/{bob['id']}").status_code == 409


def test_delete_person_used_as_percentage_participant_is_rejected(
    client: TestClient,
) -> None:
    alice = add_person(client, "Alice")
    bob = add_person(client, "Bob")
    client.post(
        "/api/expenses",
        json={
            "description": "Hotel",
            "amount": "100.00",
            "payer_id": alice["id"],
            "split_type": "percentage",
            "percentages": {str(bob["id"]): "100"},
        },
    )

    assert client.delete(f"/api/people/{bob['id']}").status_code == 409


def test_deleted_person_id_is_not_reused_and_name_can_be_readded(
    client: TestClient,
) -> None:
    alice = add_person(client, "Alice")
    add_person(client, "Bob")
    client.delete(f"/api/people/{alice['id']}")

    new_alice = add_person(client, "Alice")

    assert new_alice == {"id": 3, "name": "Alice"}
    assert client.get("/api/people").json() == [
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Alice"},
    ]


def test_person_can_be_removed_after_referencing_expense_is_deleted(
    client: TestClient,
) -> None:
    alice = add_person(client, "Alice")
    bob = add_person(client, "Bob")
    client.post(
        "/api/expenses",
        json=equal_expense(int(alice["id"]), [int(bob["id"])]),
    )
    client.delete("/api/expenses/1")

    assert client.delete(f"/api/people/{bob['id']}").status_code == 204


def test_reset_session_clears_all_derived_and_stored_data(
    client: TestClient,
) -> None:
    alice = add_person(client, "Alice")
    bob = add_person(client, "Bob")
    client.post(
        "/api/expenses",
        json=equal_expense(
            int(alice["id"]),
            [int(alice["id"]), int(bob["id"])],
        ),
    )
    client.post(
        "/api/expenses",
        json=equal_expense(
            int(alice["id"]),
            [int(alice["id"]), int(bob["id"])],
            amount="40.00",
        ),
    )
    assert client.get("/api/balances").json()[0]["balance_cents"] != 0
    assert client.get("/api/settlements").json()

    response = client.delete("/api/session")

    assert response.status_code == 204
    assert client.get("/api/people").json() == []
    assert client.get("/api/expenses").json() == []
    assert client.get("/api/balances").json() == []
    assert client.get("/api/settlements").json() == []


def test_reset_session_restarts_person_and_expense_ids(client: TestClient) -> None:
    alice = add_person(client, "Alice")
    client.post(
        "/api/expenses",
        json=equal_expense(int(alice["id"]), [int(alice["id"])]),
    )
    add_person(client, "Bob")
    client.post(
        "/api/expenses",
        json=equal_expense(int(alice["id"]), [int(alice["id"])]),
    )

    client.delete("/api/session")
    new_person = add_person(client, "Carol")
    new_expense = client.post(
        "/api/expenses",
        json=equal_expense(int(new_person["id"]), [int(new_person["id"])]),
    ).json()

    assert new_person["id"] == 1
    assert new_expense["id"] == 1
