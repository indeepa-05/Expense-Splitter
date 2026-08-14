"""Exact parsing and display formatting for monetary values."""

from decimal import Decimal, InvalidOperation


class InvalidMoneyError(ValueError):
    """Raised when a value cannot represent a positive expense amount."""


def parse_money_to_cents(value: str) -> int:
    """Parse a positive decimal money string into an exact integer cent value."""
    if not isinstance(value, str):
        raise InvalidMoneyError("Money value must be provided as text")

    cleaned_value = value.strip()
    if not cleaned_value:
        raise InvalidMoneyError("Money value must not be empty")

    try:
        amount = Decimal(cleaned_value)
    except InvalidOperation as error:
        raise InvalidMoneyError("Money value must be a valid decimal number") from error

    if not amount.is_finite():
        raise InvalidMoneyError("Money value must be a finite decimal number")
    if amount <= 0:
        raise InvalidMoneyError("Money value must be greater than zero")
    if amount.as_tuple().exponent < -2:
        raise InvalidMoneyError("Money value must have no more than two decimal places")

    return int(amount * 100)


def format_cents(amount_cents: int) -> str:
    """Format an integer number of cents as a rupee display string."""
    if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
        raise TypeError("Amount in cents must be an integer")

    absolute_cents = abs(amount_cents)
    rupees, cents = divmod(absolute_cents, 100)
    sign = "-" if amount_cents < 0 else ""
    return f"{sign}Rs. {rupees:,}.{cents:02d}"
