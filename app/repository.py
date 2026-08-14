"""In-memory persistence for people."""

from app.models import Person


class InvalidPersonNameError(ValueError):
    """Raised when a person's cleaned name is empty."""


class DuplicatePersonError(ValueError):
    """Raised when a person with the same normalized name already exists."""


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

    def reset(self) -> None:
        """Clear all people and restart IDs, primarily for test isolation."""
        self._people: list[Person] = []
        self._next_id = 1


people_repository = PeopleRepository()
