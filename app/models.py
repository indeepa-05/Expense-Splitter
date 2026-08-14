"""API models for the Expense Splitter."""

from enum import Enum

from pydantic import BaseModel


class PersonCreate(BaseModel):
    """Data required to create a person."""

    name: str


class Person(BaseModel):
    """A person participating in the current session."""

    id: int
    name: str


class SplitType(str, Enum):
    """Supported expense allocation methods."""

    EQUAL = "equal"
    PERCENTAGE = "percentage"


class ExpenseRequest(BaseModel):
    """Input accepted when creating or replacing an expense."""

    description: str = ""
    amount: str
    payer_id: int
    split_type: SplitType
    participant_ids: list[int] | None = None
    percentages: dict[int, str] | None = None


class ExpenseDetails(BaseModel):
    """Validated expense data before repository ID assignment."""

    description: str
    amount_cents: int
    payer_id: int
    participant_ids: list[int]
    split_type: SplitType
    shares: dict[int, int]
    percentages: dict[int, str] | None = None


class Expense(ExpenseDetails):
    """A stored expense in the current application session."""

    id: int


class BalanceStatus(str, Enum):
    """A person's current net accounting position."""

    RECEIVE = "receive"
    OWES = "owes"
    SETTLED = "settled"


class BalanceResponse(BaseModel):
    """Derived balance information returned by the API."""

    person_id: int
    name: str
    balance_cents: int
    balance: str
    status: BalanceStatus


class SettlementTransaction(BaseModel):
    """An exact payment from a debtor to a creditor."""

    from_person_id: int
    to_person_id: int
    amount_cents: int


class SettlementResponse(SettlementTransaction):
    """A settlement transaction enriched for API display."""

    from_name: str
    to_name: str
    amount: str
