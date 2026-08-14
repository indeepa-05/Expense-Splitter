"""Tests for derived running balances and the balances API."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Expense, Person, SplitType
from app.repository import expense_repository, people_repository
from app.services.balances import BalanceIntegrityError, calculate_balances
from app.services.splits import calculate_equal_split


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


def add_people(client: TestClient, *names: str) -> dict[str, int]:
    return {
        name: client.post("/api/people", json={"name": name}).json()["id"]
        for name in names
    }


def equal_request(
    payer_id: int,
    participant_ids: list[int],
    amount: str,
) -> dict[str, object]:
    return {
        "description": "Test expense",
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "equal",
        "participant_ids": participant_ids,
    }


def percentage_request(
    payer_id: int,
    percentages: dict[int, str],
    amount: str,
) -> dict[str, object]:
    return {
        "description": "Test expense",
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "percentage",
        "percentages": percentages,
    }


def balance_map(client: TestClient) -> dict[int, int]:
    response = client.get("/api/balances")
    assert response.status_code == 200
    return {
        item["person_id"]: item["balance_cents"]
        for item in response.json()
    }


def test_balances_empty_group(client: TestClient) -> None:
    assert client.get("/api/balances").json() == []


def test_balances_people_without_expenses_are_zero(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol")

    assert balance_map(client) == {person_id: 0 for person_id in people.values()}


def test_simple_equal_expense_balances(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values()), "100.00"),
    )

    balances = balance_map(client)

    assert balances == {people["Alice"]: 5000, people["Bob"]: -5000}
    assert sum(balances.values()) == 0


def test_payer_outside_participants(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol")
    client.post(
        "/api/expenses",
        json=equal_request(
            people["Alice"],
            [people["Bob"], people["Carol"]],
            "100.00",
        ),
    )

    assert balance_map(client) == {
        people["Alice"]: 10000,
        people["Bob"]: -5000,
        people["Carol"]: -5000,
    }


def test_multiple_expenses_accumulate(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    participants = list(people.values())
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], participants, "100.00"),
    )
    client.post(
        "/api/expenses",
        json=equal_request(people["Bob"], participants, "40.00"),
    )

    assert balance_map(client) == {people["Alice"]: 3000, people["Bob"]: -3000}


def test_balances_api_includes_names_format_and_status(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol")
    client.post(
        "/api/expenses",
        json=equal_request(
            people["Alice"],
            [people["Alice"], people["Bob"]],
            "100.00",
        ),
    )

    assert client.get("/api/balances").json() == [
        {
            "person_id": people["Alice"],
            "name": "Alice",
            "balance_cents": 5000,
            "balance": "Rs. 50.00",
            "status": "receive",
        },
        {
            "person_id": people["Bob"],
            "name": "Bob",
            "balance_cents": -5000,
            "balance": "-Rs. 50.00",
            "status": "owes",
        },
        {
            "person_id": people["Carol"],
            "name": "Carol",
            "balance_cents": 0,
            "balance": "Rs. 0.00",
            "status": "settled",
        },
    ]


def test_assignment_sanity_check_balances(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol", "Dave")
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values()), "12000.00"),
    )
    client.post(
        "/api/expenses",
        json=percentage_request(
            people["Carol"],
            {
                people["Alice"]: "33.33",
                people["Bob"]: "33.33",
                people["Dave"]: "33.34",
            },
            "10000.00",
        ),
    )
    client.post(
        "/api/expenses",
        json=equal_request(
            people["Dave"],
            [people["Dave"], people["Bob"]],
            "6000.00",
        ),
    )

    balances = balance_map(client)

    assert balances == {
        people["Alice"]: 566700,
        people["Bob"]: -933300,
        people["Carol"]: 700000,
        people["Dave"]: -333400,
    }
    assert sum(balances.values()) == 0


def test_edit_amount_recalculates_balances(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    participants = list(people.values())
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], participants, "100.00"),
    )
    client.put(
        "/api/expenses/1",
        json=equal_request(people["Alice"], participants, "200.00"),
    )

    assert balance_map(client) == {people["Alice"]: 10000, people["Bob"]: -10000}


def test_change_payer_recalculates_balances(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    participants = list(people.values())
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], participants, "100.00"),
    )
    client.put(
        "/api/expenses/1",
        json=equal_request(people["Bob"], participants, "100.00"),
    )

    assert balance_map(client) == {people["Alice"]: -5000, people["Bob"]: 5000}


def test_change_participants_recalculates_balances(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol")
    client.post(
        "/api/expenses",
        json=equal_request(
            people["Alice"],
            [people["Alice"], people["Bob"]],
            "100.00",
        ),
    )
    client.put(
        "/api/expenses/1",
        json=equal_request(
            people["Alice"],
            [people["Bob"], people["Carol"]],
            "100.00",
        ),
    )

    assert balance_map(client) == {
        people["Alice"]: 10000,
        people["Bob"]: -5000,
        people["Carol"]: -5000,
    }


def test_switch_split_type_recalculates_balances(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values()), "100.00"),
    )
    client.put(
        "/api/expenses/1",
        json=percentage_request(
            people["Alice"],
            {people["Alice"]: "75", people["Bob"]: "25"},
            "100.00",
        ),
    )

    assert balance_map(client) == {people["Alice"]: 2500, people["Bob"]: -2500}


def test_delete_expense_recalculates_balances(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values()), "100.00"),
    )
    client.delete("/api/expenses/1")

    assert balance_map(client) == {people["Alice"]: 0, people["Bob"]: 0}


def test_balance_invariant_over_many_valid_expenses() -> None:
    for participant_count in range(1, 11):
        people = [
            Person(id=person_id, name=f"Person {person_id}")
            for person_id in range(1, participant_count + 1)
        ]
        for total_cents in [1, 2, 7, 99, 100, 1001, 9999]:
            participant_ids = [person.id for person in people]
            expense = Expense(
                id=1,
                description="Invariant test",
                amount_cents=total_cents,
                payer_id=1,
                participant_ids=participant_ids,
                split_type=SplitType.EQUAL,
                shares=calculate_equal_split(total_cents, participant_ids),
            )

            assert sum(calculate_balances(people, [expense]).values()) == 0


def test_corrupted_expense_is_rejected() -> None:
    people = [Person(id=1, name="Alice"), Person(id=2, name="Bob")]
    corrupted = Expense(
        id=1,
        description="Corrupted",
        amount_cents=100,
        payer_id=1,
        participant_ids=[1, 2],
        split_type=SplitType.EQUAL,
        shares={1: 50, 2: 49},
    )

    with pytest.raises(BalanceIntegrityError):
        calculate_balances(people, [corrupted])
