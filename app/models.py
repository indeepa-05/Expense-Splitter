"""API models for people managed by the Expense Splitter."""

from pydantic import BaseModel


class PersonCreate(BaseModel):
    """Data required to create a person."""

    name: str


class Person(BaseModel):
    """A person participating in the current session."""

    id: int
    name: str
