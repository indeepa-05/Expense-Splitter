"""Exact split calculations using integer cents."""

from decimal import Decimal, InvalidOperation, ROUND_FLOOR


class InvalidEqualSplitError(ValueError):
    """Raised when an equal split cannot be calculated from the inputs."""


class InvalidPercentageError(ValueError):
    """Raised when a percentage or percentage split is invalid."""


def parse_percentage(value: str) -> Decimal:
    """Parse a percentage string with at most two decimal places."""
    if not isinstance(value, str):
        raise InvalidPercentageError("Percentage must be provided as text")

    cleaned_value = value.strip()
    if not cleaned_value:
        raise InvalidPercentageError("Percentage must not be empty")

    try:
        percentage = Decimal(cleaned_value)
    except InvalidOperation as error:
        raise InvalidPercentageError("Percentage must be a valid decimal number") from error

    if not percentage.is_finite():
        raise InvalidPercentageError("Percentage must be finite")
    if percentage <= 0:
        raise InvalidPercentageError("Percentage must be greater than zero")
    if percentage > Decimal("100"):
        raise InvalidPercentageError("Percentage must not exceed 100")
    if percentage.as_tuple().exponent < -2:
        raise InvalidPercentageError(
            "Percentage must have no more than two decimal places"
        )

    return percentage


def calculate_equal_split(
    total_cents: int,
    participant_ids: list[int],
) -> dict[int, int]:
    """Split positive cents equally, assigning remainder cents in input order."""
    if not isinstance(total_cents, int) or isinstance(total_cents, bool):
        raise InvalidEqualSplitError("Total cents must be an integer")
    if total_cents <= 0:
        raise InvalidEqualSplitError("Total cents must be greater than zero")
    if not participant_ids:
        raise InvalidEqualSplitError("At least one participant is required")
    if any(
        not isinstance(participant_id, int) or isinstance(participant_id, bool)
        for participant_id in participant_ids
    ):
        raise InvalidEqualSplitError("Participant IDs must be integers")
    if len(set(participant_ids)) != len(participant_ids):
        raise InvalidEqualSplitError("Participant IDs must not contain duplicates")

    base_share, remainder = divmod(total_cents, len(participant_ids))
    return {
        participant_id: base_share + (position < remainder)
        for position, participant_id in enumerate(participant_ids)
    }


def calculate_percentage_split(
    total_cents: int,
    percentages: dict[int, Decimal],
) -> dict[int, int]:
    """Split cents by exact percentages using the largest remainder method."""
    if not isinstance(total_cents, int) or isinstance(total_cents, bool):
        raise InvalidPercentageError("Total cents must be an integer")
    if total_cents <= 0:
        raise InvalidPercentageError("Total cents must be greater than zero")
    if not percentages:
        raise InvalidPercentageError("At least one percentage is required")

    participant_ids = list(percentages)
    if any(
        not isinstance(participant_id, int) or isinstance(participant_id, bool)
        for participant_id in participant_ids
    ):
        raise InvalidPercentageError("Participant IDs must be integers")
    if len(set(participant_ids)) != len(participant_ids):
        raise InvalidPercentageError("Participant IDs must not contain duplicates")

    percentage_values = list(percentages.values())
    for percentage in percentage_values:
        if not isinstance(percentage, Decimal):
            raise InvalidPercentageError("Percentages must use Decimal values")
        if not percentage.is_finite():
            raise InvalidPercentageError("Percentages must be finite")
        if percentage <= 0:
            raise InvalidPercentageError("Percentages must be greater than zero")
        if percentage > Decimal("100"):
            raise InvalidPercentageError("Percentages must not exceed 100")
        if percentage.as_tuple().exponent < -2:
            raise InvalidPercentageError(
                "Percentages must have no more than two decimal places"
            )

    if sum(percentage_values, Decimal("0")) != Decimal("100"):
        raise InvalidPercentageError("Percentages must total exactly 100")

    exact_shares = [
        Decimal(total_cents) * percentage / Decimal("100")
        for percentage in percentage_values
    ]
    floor_shares = [
        int(exact_share.to_integral_value(rounding=ROUND_FLOOR))
        for exact_share in exact_shares
    ]
    fractional_remainders = [
        exact_share - floor_share
        for exact_share, floor_share in zip(exact_shares, floor_shares)
    ]
    remaining_cents = total_cents - sum(floor_shares)

    allocation_order = sorted(
        range(len(participant_ids)),
        key=lambda position: (-fractional_remainders[position], position),
    )
    for position in allocation_order[:remaining_cents]:
        floor_shares[position] += 1

    return dict(zip(participant_ids, floor_shares))
