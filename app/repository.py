"""In-memory persistence for people."""

from app.models import Expense, ExpenseDetails, Person


class InvalidPersonNameError(ValueError):
    """Raised when a person's cleaned name is empty."""


class DuplicatePersonError(ValueError):
    """Raised when a person with the same normalized name already exists."""


class PersonNotFoundError(LookupError):
    """Raised when a person ID is not present in the repository."""


class PeopleRepository:
    """Store people in insertion order for the lifetime of the application."""

    def __init__(self) -> None:
        self.reset()

    def add(self, name: str) -> Person:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise InvalidPersonNameError("Person name must not be empty")

        normalized_name = cleaned_name.casefold()
        if any(person.name.casefold() == normalized_name for person in self._people):
            raise DuplicatePersonError("A person with this name already exists")

        person = Person(id=self._next_id, name=cleaned_name)
        self._people.append(person)
        self._next_id += 1
        return person

    def list_all(self) -> list[Person]:
        return list(self._people)

    def get(self, person_id: int) -> Person:
        for person in self._people:
            if person.id == person_id:
                return person
        raise PersonNotFoundError(f"Person {person_id} does not exist")

    def delete(self, person_id: int) -> None:
        for position, person in enumerate(self._people):
            if person.id == person_id:
                del self._people[position]
                return
        raise PersonNotFoundError(f"Person {person_id} does not exist")

    def exists(self, person_id: int) -> bool:
        return any(person.id == person_id for person in self._people)

    def reset(self) -> None:
        """Clear all people and restart IDs, primarily for test isolation."""
        self._people: list[Person] = []
        self._next_id = 1


people_repository = PeopleRepository()


class ExpenseNotFoundError(LookupError):
    """Raised when an expense ID is not present in the repository."""


class ExpenseRepository:
    """Store expenses in insertion order for the application lifetime."""

    def __init__(self) -> None:
        self.reset()

    def add(self, details: ExpenseDetails) -> Expense:
        expense = self._to_expense(self._next_id, details)
        self._expenses.append(expense)
        self._next_id += 1
        return expense

    def list_all(self) -> list[Expense]:
        return list(self._expenses)

    def get(self, expense_id: int) -> Expense:
        for expense in self._expenses:
            if expense.id == expense_id:
                return expense
        raise ExpenseNotFoundError(f"Expense {expense_id} does not exist")

    def update(self, expense_id: int, details: ExpenseDetails) -> Expense:
        for position, expense in enumerate(self._expenses):
            if expense.id == expense_id:
                updated_expense = self._to_expense(expense_id, details)
                self._expenses[position] = updated_expense
                return updated_expense
        raise ExpenseNotFoundError(f"Expense {expense_id} does not exist")

    def delete(self, expense_id: int) -> None:
        for position, expense in enumerate(self._expenses):
            if expense.id == expense_id:
                del self._expenses[position]
                return
        raise ExpenseNotFoundError(f"Expense {expense_id} does not exist")

    def reset(self) -> None:
        """Clear expenses and restart IDs, primarily for test isolation."""
        self._expenses: list[Expense] = []
        self._next_id = 1

    @staticmethod
    def _to_expense(expense_id: int, details: ExpenseDetails) -> Expense:
        return Expense(
            id=expense_id,
            description=details.description,
            amount_cents=details.amount_cents,
            payer_id=details.payer_id,
            participant_ids=list(details.participant_ids),
            split_type=details.split_type,
            shares=dict(details.shares),
            percentages=(
                dict(details.percentages) if details.percentages is not None else None
            ),
        )


expense_repository = ExpenseRepository()
