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
