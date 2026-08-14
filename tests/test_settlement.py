"""Tests for exact optimal settlement calculation and API integration."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import SettlementTransaction
from app.repository import expense_repository, people_repository
from app.services.settlement import (
    InvalidSettlementBalancesError,
    calculate_optimal_settlement,
)


def apply_transactions(
    balances: dict[int, int],
    transactions: list[SettlementTransaction],
) -> dict[int, int]:
    remaining = balances.copy()
    for transaction in transactions:
        assert transaction.amount_cents > 0
        assert transaction.from_person_id != transaction.to_person_id
        remaining[transaction.from_person_id] += transaction.amount_cents
        remaining[transaction.to_person_id] -= transaction.amount_cents
    return remaining


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
        "description": "Settlement test",
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "equal",
        "participant_ids": participant_ids,
    }


def test_settlement_empty_and_already_settled_balances() -> None:
    assert calculate_optimal_settlement({}) == []
    assert calculate_optimal_settlement({1: 0, 2: 0, 3: 0}) == []


def test_settlement_single_debtor_creditor() -> None:
    transactions = calculate_optimal_settlement({1: 5000, 2: -5000})

    assert transactions == [
        SettlementTransaction(
            from_person_id=2,
            to_person_id=1,
            amount_cents=5000,
        )
    ]


@pytest.mark.parametrize(
    ("balances", "expected_count"),
    [
        ({1: 7000, 2: 3000, 3: -10000}, 2),
        ({1: 10000, 2: -4000, 3: -6000}, 2),
    ],
)
def test_settlement_multiple_debtors_or_creditors(
    balances: dict[int, int],
    expected_count: int,
) -> None:
    transactions = calculate_optimal_settlement(balances)

    assert len(transactions) == expected_count
    assert all(value == 0 for value in apply_transactions(balances, transactions).values())


def test_settlement_zeroes_all_balances_and_has_valid_transactions() -> None:
    balances = {1: 900, 2: -400, 3: -300, 4: -200, 5: 0}

    transactions = calculate_optimal_settlement(balances)

    assert all(value == 0 for value in apply_transactions(balances, transactions).values())
    assert all(transaction.amount_cents > 0 for transaction in transactions)
    assert all(
        balances[transaction.from_person_id] < 0
        and balances[transaction.to_person_id] > 0
        for transaction in transactions
    )


def test_settlement_does_not_mutate_input() -> None:
    balances = {1: 7000, 2: -2000, 3: -5000}
    original = balances.copy()

    calculate_optimal_settlement(balances)

    assert balances == original


@pytest.mark.parametrize(
    "balances",
    [
        {1: 100, 2: -99},
        {1: 10, 2: -10.0},
        {1: True, 2: -1},
    ],
)
def test_settlement_rejects_invalid_balances(balances: dict[int, int]) -> None:
    with pytest.raises(InvalidSettlementBalancesError):
        calculate_optimal_settlement(balances)


def test_settlement_is_deterministic_with_lexicographic_ties() -> None:
    balances = {1: -50, 2: -50, 3: 50, 4: 50}

    first = calculate_optimal_settlement(balances)
    second = calculate_optimal_settlement(balances)

    assert first == second
    assert [
        (item.from_person_id, item.to_person_id, item.amount_cents)
        for item in first
    ] == [(1, 3, 50), (2, 4, 50)]


def test_optimal_settlement_beats_greedy_counterexample() -> None:
    balances = {1: -800, 2: -700, 3: 200, 4: 600, 5: 700}

    transactions = calculate_optimal_settlement(balances)

    assert len(transactions) == 3
    assert all(value == 0 for value in apply_transactions(balances, transactions).values())


def test_assignment_scenario_requires_three_transactions() -> None:
    balances = {1: 566700, 2: -933300, 3: 700000, 4: -333400}

    transactions = calculate_optimal_settlement(balances)

    assert len(transactions) == 3
    assert all(value == 0 for value in apply_transactions(balances, transactions).values())


def test_settlement_api_empty_when_settled(client: TestClient) -> None:
    add_people(client, "Alice", "Bob")

    assert client.get("/api/settlements").json() == []


def test_settlement_api_includes_names_and_formatted_amount(
    client: TestClient,
) -> None:
    people = add_people(client, "Alice", "Bob")
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values()), "100.00"),
    )

    response = client.get("/api/settlements")

    assert response.status_code == 200
    assert response.json() == [
        {
            "from_person_id": people["Bob"],
            "from_name": "Bob",
            "to_person_id": people["Alice"],
            "to_name": "Alice",
            "amount_cents": 5000,
            "amount": "Rs. 50.00",
        }
    ]


def test_edit_expense_recalculates_settlement(client: TestClient) -> None:
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

    settlement = client.get("/api/settlements").json()

    assert settlement[0]["amount_cents"] == 10000


def test_change_payer_reverses_settlement(client: TestClient) -> None:
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

    settlement = client.get("/api/settlements").json()[0]

    assert settlement["from_person_id"] == people["Alice"]
    assert settlement["to_person_id"] == people["Bob"]
    assert settlement["amount_cents"] == 5000


def test_delete_expense_clears_settlement(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    client.post(
        "/api/expenses",
        json=equal_request(people["Alice"], list(people.values()), "100.00"),
    )
    assert client.get("/api/settlements").json()

    client.delete("/api/expenses/1")

    assert client.get("/api/settlements").json() == []
