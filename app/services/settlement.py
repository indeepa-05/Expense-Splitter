"""Exact minimum-transaction settlement calculations."""

from collections.abc import Sequence
from functools import lru_cache

from app.models import Expense, Person, SettlementResponse, SettlementTransaction
from app.services.balances import calculate_balances
from app.services.money import format_cents


class InvalidSettlementBalancesError(ValueError):
    """Raised when balances cannot be settled exactly."""


BalanceState = tuple[tuple[int, int], ...]
TransactionTuple = tuple[int, int, int]
TransactionPlan = tuple[TransactionTuple, ...]


def calculate_optimal_settlement(
    balances: dict[int, int],
) -> list[SettlementTransaction]:
    """Return a deterministic globally minimum transaction settlement plan."""
    if any(
        not isinstance(balance, int) or isinstance(balance, bool)
        for balance in balances.values()
    ):
        raise InvalidSettlementBalancesError("Balances must use integer cents")
    if sum(balances.values()) != 0:
        raise InvalidSettlementBalancesError("Balances must sum exactly to zero")

    initial_state: BalanceState = tuple(
        (person_id, balance)
        for person_id, balance in balances.items()
        if balance != 0
    )

    @lru_cache(maxsize=None)
    def solve(state: BalanceState) -> TransactionPlan:
        if not state:
            return ()

        first_id, first_balance = state[0]
        candidate_positions = [
            position
            for position in range(1, len(state))
            if first_balance * state[position][1] < 0
        ]
        candidate_positions.sort(
            key=lambda position: (
                state[position][1] != -first_balance,
                position,
            )
        )

        best_plan: TransactionPlan | None = None
        for position in candidate_positions:
            other_id, other_balance = state[position]
            amount_cents = min(abs(first_balance), abs(other_balance))
            next_state = list(state)

            if first_balance < 0:
                transaction = (first_id, other_id, amount_cents)
                next_state[0] = (first_id, first_balance + amount_cents)
                next_state[position] = (other_id, other_balance - amount_cents)
            else:
                transaction = (other_id, first_id, amount_cents)
                next_state[0] = (first_id, first_balance - amount_cents)
                next_state[position] = (other_id, other_balance + amount_cents)

            unsettled_state = tuple(
                entry for entry in next_state if entry[1] != 0
            )
            candidate_plan = tuple(
                sorted((transaction, *solve(unsettled_state)))
            )

            if best_plan is None or (len(candidate_plan), candidate_plan) < (
                len(best_plan),
                best_plan,
            ):
                best_plan = candidate_plan

        if best_plan is None:
            raise InvalidSettlementBalancesError(
                "Balances do not contain a valid debtor-creditor pairing"
            )
        return best_plan

    plan = solve(initial_state)
    return [
        SettlementTransaction(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            amount_cents=amount_cents,
        )
        for from_person_id, to_person_id, amount_cents in plan
    ]


def build_settlement_responses(
    people: Sequence[Person],
    expenses: Sequence[Expense],
) -> list[SettlementResponse]:
    """Derive current balances and return their optimal settlement plan."""
    balances = calculate_balances(people, expenses)
    transactions = calculate_optimal_settlement(balances)
    names = {person.id: person.name for person in people}
    return [
        SettlementResponse(
            from_person_id=transaction.from_person_id,
            from_name=names[transaction.from_person_id],
            to_person_id=transaction.to_person_id,
            to_name=names[transaction.to_person_id],
            amount_cents=transaction.amount_cents,
            amount=format_cents(transaction.amount_cents),
        )
        for transaction in transactions
    ]
