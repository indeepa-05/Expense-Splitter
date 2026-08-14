# Expense Splitter

A minimal FastAPI foundation for an Expense Splitter application.

## Implemented features

- Add people with validated, unique names
- List people in insertion order
- In-memory storage for the current application session
- Safe monetary calculations using integer cents instead of binary floating point
- Exact equal splits with deterministic remainder distribution

For example, splitting Rs. 100.00 among three people produces Rs. 33.34,
Rs. 33.33, and Rs. 33.33 in participant order. The integer-cent shares still
total exactly Rs. 100.00.

## Run

```sh
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```sh
python -m pytest -v
```
