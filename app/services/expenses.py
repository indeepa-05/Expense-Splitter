"""Expense validation and orchestration."""

from decimal import Decimal

from app.models import Expense, ExpenseDetails, ExpenseRequest, SplitType
from app.repository import (
    ExpenseNotFoundError,
    expense_repository,
    people_repository,
)
from app.services.money import InvalidMoneyError, parse_money_to_cents
from app.services.splits import (
    InvalidEqualSplitError,
    InvalidPercentageError,
    calculate_equal_split,
    calculate_percentage_split,
    parse_percentage,
)


class ExpenseValidationError(ValueError):
    """Raised when submitted expense data is inconsistent or invalid."""


def create_expense(request: ExpenseRequest) -> Expense:
    """Validate, calculate, and store a new expense."""
    return expense_repository.add(_build_expense_details(request))


def list_expenses() -> list[Expense]:
    return expense_repository.list_all()


def get_expense(expense_id: int) -> Expense:
    return expense_repository.get(expense_id)


def update_expense(expense_id: int, request: ExpenseRequest) -> Expense:
    """Fully replace an expense after recalculating its shares."""
    expense_repository.get(expense_id)
    return expense_repository.update(expense_id, _build_expense_details(request))


def delete_expense(expense_id: int) -> None:
    expense_repository.delete(expense_id)


def _build_expense_details(request: ExpenseRequest) -> ExpenseDetails:
    if not people_repository.exists(request.payer_id):
        raise ExpenseValidationError(f"Payer {request.payer_id} does not exist")

    try:
        amount_cents = parse_money_to_cents(request.amount)
        if request.split_type == SplitType.EQUAL:
            participant_ids, shares, percentages = _build_equal_split(
                amount_cents,
                request,
            )
        else:
            participant_ids, shares, percentages = _build_percentage_split(
                amount_cents,
                request,
            )
    except (InvalidMoneyError, InvalidEqualSplitError, InvalidPercentageError) as error:
        raise ExpenseValidationError(str(error)) from error

    if sum(shares.values()) != amount_cents:
        raise RuntimeError("Expense shares do not match the expense amount")

    return ExpenseDetails(
        description=request.description.strip(),
        amount_cents=amount_cents,
        payer_id=request.payer_id,
        participant_ids=participant_ids,
        split_type=request.split_type,
        shares=shares,
        percentages=percentages,
    )


def _build_equal_split(
    amount_cents: int,
    request: ExpenseRequest,
) -> tuple[list[int], dict[int, int], None]:
    if request.percentages is not None:
        raise ExpenseValidationError(
            "Percentages must not be provided for an equal expense"
        )
    if request.participant_ids is None:
        raise ExpenseValidationError(
            "Participant IDs are required for an equal expense"
        )

    participant_ids = list(request.participant_ids)
    _validate_people(participant_ids)
    return participant_ids, calculate_equal_split(amount_cents, participant_ids), None


def _build_percentage_split(
    amount_cents: int,
    request: ExpenseRequest,
) -> tuple[list[int], dict[int, int], dict[int, str]]:
    if request.participant_ids is not None:
        raise ExpenseValidationError(
            "Participant IDs must not be provided for a percentage expense"
        )
    if request.percentages is None:
        raise ExpenseValidationError(
            "Percentages are required for a percentage expense"
        )

    parsed_percentages: dict[int, Decimal] = {
        participant_id: parse_percentage(value)
        for participant_id, value in request.percentages.items()
    }
    participant_ids = list(parsed_percentages)
    _validate_people(participant_ids)
    shares = calculate_percentage_split(amount_cents, parsed_percentages)
    stored_percentages = {
        participant_id: str(percentage)
        for participant_id, percentage in parsed_percentages.items()
    }
    return participant_ids, shares, stored_percentages


def _validate_people(participant_ids: list[int]) -> None:
    for participant_id in participant_ids:
        if not people_repository.exists(participant_id):
            raise ExpenseValidationError(
                f"Participant {participant_id} does not exist"
            )
