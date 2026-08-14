"""FastAPI entry point for the Expense Splitter application."""

from fastapi import FastAPI, HTTPException, status

from app.models import Person, PersonCreate
from app.repository import (
    DuplicatePersonError,
    InvalidPersonNameError,
    people_repository,
)


app = FastAPI(title="Expense Splitter")


@app.get("/")
def read_root() -> dict[str, str]:
    """Identify the application."""
    return {"name": "Expense Splitter"}


@app.get("/api/health")
def read_health() -> dict[str, str]:
    """Report whether the API is available."""
    return {"status": "ok"}


@app.post("/api/people", response_model=Person, status_code=status.HTTP_201_CREATED)
def add_person(person_data: PersonCreate) -> Person:
    """Add a person to the current application session."""
    try:
        return people_repository.add(person_data.name)
    except (InvalidPersonNameError, DuplicatePersonError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@app.get("/api/people", response_model=list[Person])
def list_people() -> list[Person]:
    """Return people in the order they were added."""
    return people_repository.list_all()
