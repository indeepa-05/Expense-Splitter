"""End-to-end API regression tests for the complete Expense Splitter workflow."""

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


def add_people(client: TestClient, *names: str) -> dict[str, int]:
    people: dict[str, int] = {}
    for name in names:
        response = client.post("/api/people", json={"name": name})
        assert response.status_code == 201
        people[name] = response.json()["id"]
    return people


def equal_request(
    description: str,
    amount: str,
    payer_id: int,
    participant_ids: list[int],
) -> dict[str, object]:
    return {
        "description": description,
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "equal",
        "participant_ids": participant_ids,
    }


def percentage_request(
    description: str,
    amount: str,
    payer_id: int,
    percentages: dict[int, str],
) -> dict[str, object]:
    return {
        "description": description,
        "amount": amount,
        "payer_id": payer_id,
        "split_type": "percentage",
        "percentages": percentages,
    }


def current_balances(client: TestClient) -> dict[int, int]:
    return {
        item["person_id"]: item["balance_cents"]
        for item in client.get("/api/balances").json()
    }


def apply_settlements(
    balances: dict[int, int],
    settlements: list[dict[str, object]],
) -> dict[int, int]:
    remaining = balances.copy()
    for settlement in settlements:
        from_id = int(settlement["from_person_id"])
        to_id = int(settlement["to_person_id"])
        amount = int(settlement["amount_cents"])
        assert amount > 0
        assert from_id != to_id
        assert balances[from_id] < 0
        assert balances[to_id] > 0
        remaining[from_id] += amount
        remaining[to_id] -= amount
    return remaining


def test_full_assignment_workflow_through_api(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol", "Dave")
    assert len(set(people.values())) == 4
    assert [person["name"] for person in client.get("/api/people").json()] == [
        "Alice",
        "Bob",
        "Carol",
        "Dave",
    ]

    dinner = client.post(
        "/api/expenses",
        json=equal_request(
            "Dinner",
            "12000.00",
            people["Alice"],
            list(people.values()),
        ),
    )
    assert dinner.status_code == 201
    dinner_data = dinner.json()
    assert dinner_data["shares"] == {
        str(people["Alice"]): 300000,
        str(people["Bob"]): 300000,
        str(people["Carol"]): 300000,
        str(people["Dave"]): 300000,
    }
    assert sum(dinner_data["shares"].values()) == dinner_data["amount_cents"]

    hotel = client.post(
        "/api/expenses",
        json=percentage_request(
            "Hotel",
            "10000.00",
            people["Carol"],
            {
                people["Alice"]: "33.33",
                people["Bob"]: "33.33",
                people["Dave"]: "33.34",
            },
        ),
    )
    assert hotel.status_code == 201
    hotel_data = hotel.json()
    assert people["Carol"] not in hotel_data["participant_ids"]
    assert hotel_data["shares"] == {
        str(people["Alice"]): 333300,
        str(people["Bob"]): 333300,
        str(people["Dave"]): 333400,
    }
    assert sum(hotel_data["shares"].values()) == 1000000

    transport = client.post(
        "/api/expenses",
        json=equal_request(
            "Transport",
            "6000.00",
            people["Dave"],
            [people["Dave"], people["Bob"]],
        ),
    )
    assert transport.status_code == 201
    assert transport.json()["shares"] == {
        str(people["Dave"]): 300000,
        str(people["Bob"]): 300000,
    }

    balance_response = client.get("/api/balances")
    assert balance_response.status_code == 200
    balance_items = balance_response.json()
    balances = {item["person_id"]: item["balance_cents"] for item in balance_items}
    assert balances == {
        people["Alice"]: 566700,
        people["Bob"]: -933300,
        people["Carol"]: 700000,
        people["Dave"]: -333400,
    }
    assert sum(balances.values()) == 0
    assert {item["name"]: item["status"] for item in balance_items} == {
        "Alice": "receive",
        "Bob": "owes",
        "Carol": "receive",
        "Dave": "owes",
    }
    assert {item["name"]: item["balance"] for item in balance_items} == {
        "Alice": "Rs. 5,667.00",
        "Bob": "-Rs. 9,333.00",
        "Carol": "Rs. 7,000.00",
        "Dave": "-Rs. 3,334.00",
    }

    settlements = client.get("/api/settlements").json()
    assert len(settlements) == 3
    assert settlements == client.get("/api/settlements").json()
    assert all(value == 0 for value in apply_settlements(balances, settlements).values())


def test_edit_amount_and_payer_recalculates_everything(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    participants = list(people.values())
    created = client.post(
        "/api/expenses",
        json=equal_request("Dinner", "100.00", people["Alice"], participants),
    ).json()
    assert current_balances(client) == {people["Alice"]: 5000, people["Bob"]: -5000}

    updated = client.put(
        f"/api/expenses/{created['id']}",
        json=equal_request("Dinner", "200.00", people["Alice"], participants),
    )
    assert updated.status_code == 200
    assert current_balances(client) == {
        people["Alice"]: 10000,
        people["Bob"]: -10000,
    }
    assert client.get("/api/settlements").json()[0] == {
        "from_person_id": people["Bob"],
        "from_name": "Bob",
        "to_person_id": people["Alice"],
        "to_name": "Alice",
        "amount_cents": 10000,
        "amount": "Rs. 100.00",
    }

    client.put(
        f"/api/expenses/{created['id']}",
        json=equal_request("Dinner", "200.00", people["Bob"], participants),
    )
    assert current_balances(client) == {
        people["Alice"]: -10000,
        people["Bob"]: 10000,
    }
    reversed_settlement = client.get("/api/settlements").json()[0]
    assert reversed_settlement["from_person_id"] == people["Alice"]
    assert reversed_settlement["to_person_id"] == people["Bob"]
    assert reversed_settlement["amount_cents"] == 10000


def test_switch_split_modes_does_not_retain_stale_configuration(
    client: TestClient,
) -> None:
    people = add_people(client, "Alice", "Bob")
    expense = client.post(
        "/api/expenses",
        json=equal_request("Dinner", "100.00", people["Alice"], list(people.values())),
    ).json()

    percentage = client.put(
        f"/api/expenses/{expense['id']}",
        json=percentage_request(
            "Dinner",
            "100.00",
            people["Alice"],
            {people["Alice"]: "75", people["Bob"]: "25"},
        ),
    ).json()
    assert percentage["split_type"] == "percentage"
    assert percentage["shares"] == {
        str(people["Alice"]): 7500,
        str(people["Bob"]): 2500,
    }
    assert current_balances(client) == {people["Alice"]: 2500, people["Bob"]: -2500}

    equal = client.put(
        f"/api/expenses/{expense['id']}",
        json=equal_request("Dinner", "100.00", people["Alice"], list(people.values())),
    ).json()
    assert equal["split_type"] == "equal"
    assert equal["percentages"] is None
    assert equal["shares"] == {
        str(people["Alice"]): 5000,
        str(people["Bob"]): 5000,
    }
    assert current_balances(client) == {people["Alice"]: 5000, people["Bob"]: -5000}


def test_delete_expense_recalculates_balances_and_settlement(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    participants = list(people.values())
    first = client.post(
        "/api/expenses",
        json=equal_request("Dinner", "100.00", people["Alice"], participants),
    ).json()
    second = client.post(
        "/api/expenses",
        json=equal_request("Taxi", "40.00", people["Bob"], participants),
    ).json()
    before = current_balances(client)

    assert client.delete(f"/api/expenses/{second['id']}").status_code == 204
    assert [item["id"] for item in client.get("/api/expenses").json()] == [first["id"]]
    assert current_balances(client) != before
    assert current_balances(client) == {people["Alice"]: 5000, people["Bob"]: -5000}
    settlement = client.get("/api/settlements").json()
    assert len(settlement) == 1
    assert settlement[0]["amount_cents"] == 5000


def test_person_removal_reference_rules_and_id_progression(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol")
    assert client.delete(f"/api/people/{people['Carol']}").status_code == 204
    dave = client.post("/api/people", json={"name": "Dave"}).json()
    assert dave["id"] == 4

    expense = client.post(
        "/api/expenses",
        json=equal_request(
            "Dinner",
            "100.00",
            people["Alice"],
            [people["Alice"], people["Bob"]],
        ),
    ).json()
    assert client.delete(f"/api/people/{people['Alice']}").status_code == 409
    assert client.delete(f"/api/people/{people['Bob']}").status_code == 409
    client.delete(f"/api/expenses/{expense['id']}")
    assert client.delete(f"/api/people/{people['Bob']}").status_code == 204


def test_new_session_is_a_fresh_in_memory_application(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol")
    client.post(
        "/api/expenses",
        json=equal_request("Dinner", "100.00", people["Alice"], [people["Alice"], people["Bob"]]),
    )
    client.post(
        "/api/expenses",
        json=equal_request("Taxi", "60.00", people["Bob"], [people["Bob"], people["Carol"]]),
    )
    assert client.get("/api/settlements").json()

    assert client.delete("/api/session").status_code == 204
    assert client.get("/api/people").json() == []
    assert client.get("/api/expenses").json() == []
    assert client.get("/api/balances").json() == []
    assert client.get("/api/settlements").json() == []

    new_person = client.post("/api/people", json={"name": "New Alice"}).json()
    new_expense = client.post(
        "/api/expenses",
        json=equal_request("Fresh", "1.00", new_person["id"], [new_person["id"]]),
    ).json()
    assert new_person["id"] == 1
    assert new_expense["id"] == 1


def test_money_rounding_edges_through_expense_api(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol")
    equal = client.post(
        "/api/expenses",
        json=equal_request("Three ways", "100.00", people["Alice"], list(people.values())),
    ).json()
    assert equal["shares"] == {
        str(people["Alice"]): 3334,
        str(people["Bob"]): 3333,
        str(people["Carol"]): 3333,
    }
    assert sum(equal["shares"].values()) == 10000

    one_cent = client.post(
        "/api/expenses",
        json=percentage_request(
            "One cent",
            "0.01",
            people["Alice"],
            {people["Alice"]: "50", people["Bob"]: "50"},
        ),
    ).json()
    assert one_cent["shares"] == {
        str(people["Alice"]): 1,
        str(people["Bob"]): 0,
    }
    assert sum(one_cent["shares"].values()) == 1


def test_representative_invalid_requests_remain_rejected(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob")
    assert client.post("/api/people", json={"name": " alice "}).status_code == 400
    assert client.post("/api/people", json={"name": "   "}).status_code == 400

    invalid_expenses = [
        equal_request("Zero", "0", people["Alice"], [people["Alice"]]),
        equal_request("Negative", "-5", people["Alice"], [people["Alice"]]),
        equal_request("Precision", "10.999", people["Alice"], [people["Alice"]]),
        equal_request("Payer", "10", 99, [people["Alice"]]),
        equal_request("Participant", "10", people["Alice"], [99]),
        equal_request("Duplicate", "10", people["Alice"], [people["Bob"], people["Bob"]]),
        percentage_request("Low", "10", people["Alice"], {people["Alice"]: "99"}),
        percentage_request("High", "10", people["Alice"], {people["Alice"]: "100.01"}),
        percentage_request(
            "Zero percent",
            "10",
            people["Alice"],
            {people["Alice"]: "100", people["Bob"]: "0"},
        ),
        percentage_request(
            "Negative percent",
            "10",
            people["Alice"],
            {people["Alice"]: "110", people["Bob"]: "-10"},
        ),
    ]
    for request in invalid_expenses:
        assert client.post("/api/expenses", json=request).status_code == 400

    unsupported = equal_request("Unsupported", "10", people["Alice"], [people["Alice"]])
    unsupported["split_type"] = "custom"
    assert client.post("/api/expenses", json=unsupported).status_code == 422
    assert client.put("/api/expenses/99", json=invalid_expenses[0]).status_code == 404
    assert client.delete("/api/expenses/99").status_code == 404
    assert client.delete("/api/people/99").status_code == 404

    referenced = client.post(
        "/api/expenses",
        json=equal_request("Valid", "10", people["Alice"], [people["Bob"]]),
    )
    assert referenced.status_code == 201
    assert client.delete(f"/api/people/{people['Bob']}").status_code == 409


def test_end_to_end_financial_invariants(client: TestClient) -> None:
    people = add_people(client, "Alice", "Bob", "Carol", "Dave")
    requests = [
        equal_request("A", "100.00", people["Alice"], list(people.values())),
        percentage_request(
            "B",
            "87.43",
            people["Bob"],
            {people["Alice"]: "33.33", people["Carol"]: "66.67"},
        ),
        equal_request("C", "0.07", people["Dave"], [people["Bob"], people["Dave"]]),
    ]
    for request in requests:
        assert client.post("/api/expenses", json=request).status_code == 201

    expenses = client.get("/api/expenses").json()
    assert all(sum(item["shares"].values()) == item["amount_cents"] for item in expenses)
    balances = current_balances(client)
    assert sum(balances.values()) == 0
    settlements = client.get("/api/settlements").json()
    assert all(value == 0 for value in apply_settlements(balances, settlements).values())


def test_frontend_and_static_assets_smoke_through_http(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    for expected in [
        "Expense Splitter",
        "People",
        "Add Expense",
        "Equal Split",
        "Percentage Split",
        "Select All",
        "Remaining: 100.00%",
        "Expenses",
        "Balances",
        "Settle Up",
        "Start New Session",
    ]:
        assert expected in page.text
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200
