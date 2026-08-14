"""API tests for expense creation, retrieval, editing, and deletion."""

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


@pytest.fixture
def people(client: TestClient) -> dict[str, int]:
    names = ["Alice", "Bob", "Carol", "Dave"]
    return {
        name: client.post("/api/people", json={"name": name}).json()["id"]
        for name in names
    }


def equal_request(
    payer_id: int,
    participant_ids: list[int],
    *,
    description: str = "Dinner",
    amount: str = "12000.00",
) -> dict[str, object]:
    return {
        "description": description,
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "equal",
        "participant_ids": participant_ids,
    }


def percentage_request(
    payer_id: int,
    percentages: dict[str, str],
    *,
    description: str = "Hotel",
    amount: str = "10000.00",
) -> dict[str, object]:
    return {
        "description": description,
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "percentage",
        "percentages": percentages,
    }


def test_create_equal_expense(client: TestClient, people: dict[str, int]) -> None:
    response = client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values())),
    )

    assert response.status_code == 201
    expense = response.json()
    assert expense["id"] == 1
    assert expense["description"] == "Dinner"
    assert expense["amount_cents"] == 1200000
    assert expense["split_type"] == "equal"
    assert expense["percentages"] is None
    assert sum(expense["shares"].values()) == expense["amount_cents"]


def test_create_percentage_expense(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.post(
        "/api/expenses",
        json=percentage_request(
            people["Carol"],
            {
                str(people["Alice"]): "33.33",
                str(people["Bob"]): "33.33",
                str(people["Dave"]): "33.34",
            },
        ),
    )

    assert response.status_code == 201
    expense = response.json()
    assert expense["participant_ids"] == [1, 2, 4]
    assert expense["percentages"] == {"1": "33.33", "2": "33.33", "4": "33.34"}
    assert sum(expense["shares"].values()) == 1000000


def test_payer_can_be_outside_participants(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.post(
        "/api/expenses",
        json=equal_request(
            people["Alice"],
            [people["Bob"], people["Carol"]],
            amount="5000.00",
        ),
    )

    assert response.status_code == 201
    assert response.json()["participant_ids"] == [people["Bob"], people["Carol"]]


def test_create_expense_unknown_payer_rejected(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.post(
        "/api/expenses",
        json=equal_request(99, [people["Alice"]]),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Payer 99 does not exist"}


def test_create_expense_unknown_participant_rejected(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], [99]),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Participant 99 does not exist"}


def test_percentage_expense_unknown_participant_rejected(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.post(
        "/api/expenses",
        json=percentage_request(people["Alice"], {"99": "100"}),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Participant 99 does not exist"}


def test_create_expense_duplicate_participants_rejected(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.post(
        "/api/expenses",
        json=equal_request(
            people["Alice"],
            [people["Bob"], people["Bob"]],
        ),
    )

    assert response.status_code == 400


@pytest.mark.parametrize("amount", ["0", "-5", "abc", "10.999"])
def test_create_expense_invalid_amount_rejected(
    client: TestClient,
    people: dict[str, int],
    amount: str,
) -> None:
    response = client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], [people["Alice"]], amount=amount),
    )

    assert response.status_code == 400


def test_create_expense_invalid_split_type_rejected(
    client: TestClient,
    people: dict[str, int],
) -> None:
    request = equal_request(people["Alice"], [people["Alice"]])
    request["split_type"] = "random"

    assert client.post("/api/expenses", json=request).status_code == 422


def test_percentage_expense_must_total_100(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.post(
        "/api/expenses",
        json=percentage_request(
            people["Alice"],
            {str(people["Alice"]): "50", str(people["Bob"]): "49"},
        ),
    )

    assert response.status_code == 400
    assert "exactly 100" in response.json()["detail"]


def test_contradictory_split_fields_rejected(
    client: TestClient,
    people: dict[str, int],
) -> None:
    equal = equal_request(people["Alice"], [people["Alice"]])
    equal["percentages"] = {str(people["Alice"]): "100"}
    percentage = percentage_request(
        people["Alice"],
        {str(people["Alice"]): "100"},
    )
    percentage["participant_ids"] = [people["Alice"]]

    assert client.post("/api/expenses", json=equal).status_code == 400
    assert client.post("/api/expenses", json=percentage).status_code == 400


def test_split_configuration_is_required(
    client: TestClient,
    people: dict[str, int],
) -> None:
    equal = equal_request(people["Alice"], [])
    percentage = percentage_request(people["Alice"], {})

    assert client.post("/api/expenses", json=equal).status_code == 400
    assert client.post("/api/expenses", json=percentage).status_code == 400


def test_list_expenses_empty(client: TestClient) -> None:
    assert client.get("/api/expenses").json() == []


def test_expenses_list_in_insertion_order(
    client: TestClient,
    people: dict[str, int],
) -> None:
    request = equal_request(people["Alice"], [people["Alice"]])
    client.post("/api/expenses", json=request)
    client.post("/api/expenses", json=request)

    expenses = client.get("/api/expenses").json()

    assert [expense["id"] for expense in expenses] == [1, 2]


def test_get_existing_and_missing_expense(
    client: TestClient,
    people: dict[str, int],
) -> None:
    created = client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], [people["Alice"]]),
    ).json()

    assert client.get("/api/expenses/1").json() == created
    assert client.get("/api/expenses/999").status_code == 404


def test_edit_description_payer_and_preserve_id(
    client: TestClient,
    people: dict[str, int],
) -> None:
    created = client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], [people["Alice"]]),
    ).json()
    edited = client.put(
        "/api/expenses/1",
        json=equal_request(
            people["Bob"],
            [people["Alice"]],
            description="  Lunch  ",
        ),
    ).json()

    assert edited["id"] == created["id"] == 1
    assert edited["description"] == "Lunch"
    assert edited["payer_id"] == people["Bob"]
    assert sum(edited["shares"].values()) == edited["amount_cents"]


def test_edit_amount_and_equal_participants_recalculates_shares(
    client: TestClient,
    people: dict[str, int],
) -> None:
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], [people["Alice"]]),
    )
    response = client.put(
        "/api/expenses/1",
        json=equal_request(
            people["Alice"],
            [people["Alice"], people["Bob"], people["Carol"]],
            amount="100.00",
        ),
    )

    assert response.status_code == 200
    expense = response.json()
    assert expense["shares"] == {"1": 3334, "2": 3333, "3": 3333}
    assert sum(expense["shares"].values()) == expense["amount_cents"]


def test_edit_percentage_values(client: TestClient, people: dict[str, int]) -> None:
    client.post(
        "/api/expenses",
        json=percentage_request(
            people["Alice"],
            {str(people["Alice"]): "50", str(people["Bob"]): "50"},
        ),
    )
    expense = client.put(
        "/api/expenses/1",
        json=percentage_request(
            people["Alice"],
            {str(people["Alice"]): "75", str(people["Bob"]): "25"},
        ),
    ).json()

    assert expense["shares"] == {"1": 750000, "2": 250000}
    assert sum(expense["shares"].values()) == expense["amount_cents"]


def test_edit_equal_to_percentage(client: TestClient, people: dict[str, int]) -> None:
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], [people["Alice"], people["Bob"]]),
    )
    expense = client.put(
        "/api/expenses/1",
        json=percentage_request(
            people["Alice"],
            {str(people["Alice"]): "75", str(people["Bob"]): "25"},
        ),
    ).json()

    assert expense["split_type"] == "percentage"
    assert expense["percentages"] == {"1": "75", "2": "25"}
    assert sum(expense["shares"].values()) == expense["amount_cents"]


def test_edit_percentage_to_equal(client: TestClient, people: dict[str, int]) -> None:
    client.post(
        "/api/expenses",
        json=percentage_request(
            people["Alice"],
            {str(people["Alice"]): "75", str(people["Bob"]): "25"},
        ),
    )
    expense = client.put(
        "/api/expenses/1",
        json=equal_request(people["Alice"], [people["Alice"], people["Bob"]]),
    ).json()

    assert expense["split_type"] == "equal"
    assert expense["percentages"] is None
    assert expense["shares"] == {"1": 600000, "2": 600000}
    assert sum(expense["shares"].values()) == expense["amount_cents"]


def test_edit_missing_expense_returns_404(
    client: TestClient,
    people: dict[str, int],
) -> None:
    response = client.put(
        "/api/expenses/99",
        json=equal_request(people["Alice"], [people["Alice"]]),
    )

    assert response.status_code == 404


def test_delete_expense_and_missing_expense(
    client: TestClient,
    people: dict[str, int],
) -> None:
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], [people["Alice"]]),
    )

    assert client.delete("/api/expenses/1").status_code == 204
    assert client.get("/api/expenses").json() == []
    assert client.get("/api/expenses/1").status_code == 404
    assert client.delete("/api/expenses/1").status_code == 404


def test_deleted_expense_id_is_not_reused(
    client: TestClient,
    people: dict[str, int],
) -> None:
    request = equal_request(people["Alice"], [people["Alice"]])
    client.post("/api/expenses", json=request)
    client.post("/api/expenses", json=request)
    client.delete("/api/expenses/2")

    third = client.post("/api/expenses", json=request).json()

    assert third["id"] == 3


def test_assessment_expenses(client: TestClient, people: dict[str, int]) -> None:
    expense_1 = client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values())),
    ).json()
    expense_2 = client.post(
        "/api/expenses",
        json=percentage_request(
            people["Carol"],
            {
                str(people["Alice"]): "33.33",
                str(people["Bob"]): "33.33",
                str(people["Dave"]): "33.34",
            },
        ),
    ).json()
    expense_3 = client.post(
        "/api/expenses",
        json=equal_request(
            people["Dave"],
            [people["Dave"], people["Bob"]],
            amount="6000.00",
        ),
    ).json()

    assert expense_1["shares"] == {
        "1": 300000,
        "2": 300000,
        "3": 300000,
        "4": 300000,
    }
    assert sum(expense_2["shares"].values()) == 1000000
    assert expense_3["shares"] == {"4": 300000, "2": 300000}
