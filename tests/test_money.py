"""Tests for exact money parsing and formatting."""

import pytest

from app.services.money import InvalidMoneyError, format_cents, parse_money_to_cents


@pytest.mark.parametrize(
    ("value", "expected_cents"),
    [
        ("100", 10000),
        ("100.0", 10000),
        ("100.00", 10000),
        ("3333.33", 333333),
        (" 100.00 ", 10000),
        ("12000.50", 1200050),
    ],
)
def test_parse_valid_money_values(value: str, expected_cents: int) -> None:
    assert parse_money_to_cents(value) == expected_cents


@pytest.mark.parametrize("value", ["0", "0.00"])
def test_zero_money_rejected(value: str) -> None:
    with pytest.raises(InvalidMoneyError):
        parse_money_to_cents(value)


@pytest.mark.parametrize("value", ["-10", "-0.01"])
def test_negative_money_rejected(value: str) -> None:
    with pytest.raises(InvalidMoneyError):
        parse_money_to_cents(value)


@pytest.mark.parametrize("value", ["abc", "", "   ", "NaN", "Infinity"])
def test_invalid_money_string_rejected(value: str) -> None:
    with pytest.raises(InvalidMoneyError):
        parse_money_to_cents(value)


def test_more_than_two_decimal_places_rejected() -> None:
    with pytest.raises(InvalidMoneyError):
        parse_money_to_cents("10.999")


@pytest.mark.parametrize(
    ("amount_cents", "expected"),
    [
        (0, "Rs. 0.00"),
        (1, "Rs. 0.01"),
        (10000, "Rs. 100.00"),
        (1234567, "Rs. 12,345.67"),
        (-10000, "-Rs. 100.00"),
        (-933333, "-Rs. 9,333.33"),
    ],
)
def test_format_cents(amount_cents: int, expected: str) -> None:
    assert format_cents(amount_cents) == expected
