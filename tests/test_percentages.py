"""Tests for Decimal percentage parsing and exact percentage splitting."""

from decimal import Decimal

import pytest

from app.services.splits import (
    InvalidPercentageError,
    calculate_percentage_split,
    parse_percentage,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("50", Decimal("50")),
        ("33.33", Decimal("33.33")),
        (" 25.5 ", Decimal("25.5")),
    ],
)
def test_parse_valid_percentage(value: str, expected: Decimal) -> None:
    assert parse_percentage(value) == expected


@pytest.mark.parametrize("value", ["abc", "", " "])
def test_invalid_percentage_string_rejected(value: str) -> None:
    with pytest.raises(InvalidPercentageError):
        parse_percentage(value)


def test_percentage_with_too_many_decimal_places_rejected() -> None:
    with pytest.raises(InvalidPercentageError):
        parse_percentage("33.333")


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_percentage_rejected(value: str) -> None:
    with pytest.raises(InvalidPercentageError):
        parse_percentage(value)


def test_percentage_split_single_person_100_percent() -> None:
    assert calculate_percentage_split(12345, {7: Decimal("100")}) == {7: 12345}


def test_percentage_split_50_50() -> None:
    assert calculate_percentage_split(
        10000,
        {1: Decimal("50"), 2: Decimal("50")},
    ) == {1: 5000, 2: 5000}


def test_percentage_split_3333_3333_3334() -> None:
    shares = calculate_percentage_split(
        1000000,
        {
            1: Decimal("33.33"),
            2: Decimal("33.33"),
            4: Decimal("33.34"),
        },
    )

    assert shares == {1: 333300, 2: 333300, 4: 333400}
    assert sum(shares.values()) == 1000000


def test_percentage_split_small_one_cent_amount() -> None:
    assert calculate_percentage_split(
        1,
        {1: Decimal("50"), 2: Decimal("50")},
    ) == {1: 1, 2: 0}


def test_largest_remainder_allocation_uses_fraction_then_order() -> None:
    shares = calculate_percentage_split(
        2,
        {10: Decimal("34"), 30: Decimal("33"), 20: Decimal("33")},
    )

    assert shares == {10: 1, 30: 1, 20: 0}
    assert sum(shares.values()) == 2


def test_percentage_shares_sum_exactly_to_total() -> None:
    shares = calculate_percentage_split(
        99999,
        {
            1: Decimal("33.33"),
            2: Decimal("33.33"),
            3: Decimal("33.34"),
        },
    )

    assert sum(shares.values()) == 99999


@pytest.mark.parametrize(
    "percentages",
    [
        {1: Decimal("49"), 2: Decimal("50")},
        {1: Decimal("50"), 2: Decimal("50.01")},
        {1: Decimal("90"), 2: Decimal("10.01")},
    ],
)
def test_percentage_total_not_exactly_100_rejected(
    percentages: dict[int, Decimal],
) -> None:
    with pytest.raises(InvalidPercentageError):
        calculate_percentage_split(10000, percentages)


@pytest.mark.parametrize(
    "percentages",
    [
        {1: Decimal("-10"), 2: Decimal("110")},
        {1: Decimal("0"), 2: Decimal("100")},
        {1: Decimal("101"), 2: Decimal("-1")},
    ],
)
def test_invalid_individual_percentage_rejected(
    percentages: dict[int, Decimal],
) -> None:
    with pytest.raises(InvalidPercentageError):
        calculate_percentage_split(10000, percentages)


def test_direct_percentage_with_too_many_decimal_places_rejected() -> None:
    with pytest.raises(InvalidPercentageError):
        calculate_percentage_split(
            10000,
            {1: Decimal("33.333"), 2: Decimal("66.667")},
        )


def test_empty_percentage_mapping_rejected() -> None:
    with pytest.raises(InvalidPercentageError):
        calculate_percentage_split(10000, {})


def test_percentage_split_tie_break_is_deterministic() -> None:
    percentages = {20: Decimal("50"), 10: Decimal("50")}

    assert calculate_percentage_split(1, percentages) == {20: 1, 10: 0}
    assert calculate_percentage_split(1, percentages) == {20: 1, 10: 0}


def test_percentage_rounding_invariants_over_many_values() -> None:
    for total_cents in [1, 2, 3, 7, 10, 99, 100, 1001, 9999]:
        for first_percentage in range(1, 100):
            percentages = {
                1: Decimal(first_percentage),
                2: Decimal(100 - first_percentage),
            }
            shares = calculate_percentage_split(total_cents, percentages)

            assert sum(shares.values()) == total_cents
            assert all(share >= 0 for share in shares.values())
