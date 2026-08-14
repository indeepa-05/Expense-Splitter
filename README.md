# Expense Splitter

A minimal FastAPI foundation for an Expense Splitter application.

## Implemented features

- Add people with validated, unique names
- List people in insertion order
- In-memory storage for the current application session

## Run

```sh
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```sh
python -m pytest -v
```
