"""FastAPI entry point for the Expense Splitter application."""

from fastapi import FastAPI, HTTPException, status

from app.models import (
    BalanceResponse,
    Expense,
    ExpenseRequest,
    Person,
    PersonCreate,
    SettlementResponse,
)
from app.repository import (
    DuplicatePersonError,
    ExpenseNotFoundError,
    InvalidPersonNameError,
    expense_repository,
    people_repository,
)
from app.services.balances import build_balance_responses
from app.services.expenses import (
    ExpenseValidationError,
    create_expense,
    delete_expense,
    get_expense,
    list_expenses,
    update_expense,
)
from app.services.settlement import build_settlement_responses


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


@app.post(
    "/api/expenses",
    response_model=Expense,
    status_code=status.HTTP_201_CREATED,
)
def add_expense(expense_data: ExpenseRequest) -> Expense:
    """Create an expense after validating and calculating its shares."""
    try:
        return create_expense(expense_data)
    except ExpenseValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/expenses", response_model=list[Expense])
def read_expenses() -> list[Expense]:
    return list_expenses()


@app.get("/api/expenses/{expense_id}", response_model=Expense)
def read_expense(expense_id: int) -> Expense:
    try:
        return get_expense(expense_id)
    except ExpenseNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.put("/api/expenses/{expense_id}", response_model=Expense)
def replace_expense(expense_id: int, expense_data: ExpenseRequest) -> Expense:
    try:
        return update_expense(expense_id, expense_data)
    except ExpenseNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ExpenseValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete(
    "/api/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_expense(expense_id: int) -> None:
    try:
        delete_expense(expense_id)
    except ExpenseNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/balances", response_model=list[BalanceResponse])
def read_balances() -> list[BalanceResponse]:
    """Return current net balances derived from all stored expenses."""
    return build_balance_responses(
        people_repository.list_all(),
        expense_repository.list_all(),
    )


@app.get("/api/settlements", response_model=list[SettlementResponse])
def read_settlements() -> list[SettlementResponse]:
    """Return an optimal payment plan derived from current balances."""
    return build_settlement_responses(
        people_repository.list_all(),
        expense_repository.list_all(),
    )
