"""Derived zero-sum balance calculations."""

from collections.abc import Sequence

from app.models import BalanceResponse, BalanceStatus, Expense, Person
from app.services.money import format_cents


class BalanceIntegrityError(RuntimeError):
    """Raised when stored data cannot produce trustworthy balances."""


def calculate_balances(
    people: Sequence[Person],
    expenses: Sequence[Expense],
) -> dict[int, int]:
    """Derive each person's net balance in cents from all expenses.

    Positive values should be received; negative values are owed.
    """
    balances = {person.id: 0 for person in people}

    for expense in expenses:
        if sum(expense.shares.values()) != expense.amount_cents:
            raise BalanceIntegrityError(
                f"Expense {expense.id} shares do not match its amount"
            )
        if expense.payer_id not in balances:
            raise BalanceIntegrityError(
                f"Expense {expense.id} references unknown payer {expense.payer_id}"
            )

        balances[expense.payer_id] += expense.amount_cents
        for participant_id, share_cents in expense.shares.items():
            if participant_id not in balances:
                raise BalanceIntegrityError(
                    f"Expense {expense.id} references unknown participant "
                    f"{participant_id}"
                )
            balances[participant_id] -= share_cents

    if sum(balances.values()) != 0:
        raise BalanceIntegrityError("Calculated balances do not sum to zero")

    return balances


def build_balance_responses(
    people: Sequence[Person],
    expenses: Sequence[Expense],
) -> list[BalanceResponse]:
    """Build ordered API responses from current people and expenses."""
    balances = calculate_balances(people, expenses)
    return [
        BalanceResponse(
            person_id=person.id,
            name=person.name,
            balance_cents=balances[person.id],
            balance=format_cents(balances[person.id]),
            status=_balance_status(balances[person.id]),
        )
        for person in people
    ]


def _balance_status(balance_cents: int) -> BalanceStatus:
    if balance_cents > 0:
        return BalanceStatus.RECEIVE
    if balance_cents < 0:
        return BalanceStatus.OWES
    return BalanceStatus.SETTLED
