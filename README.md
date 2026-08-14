# Expense Splitter

A minimal FastAPI foundation for an Expense Splitter application.

## Implemented features

- Add people with validated, unique names
- List people in insertion order
- In-memory storage for the current application session
- Safe monetary calculations using integer cents instead of binary floating point
- Exact equal splits with deterministic remainder distribution
- Exact percentage splits using Decimal percentages and largest remainders
- Create, list, retrieve, edit, and delete expenses through the API
- Equal and percentage expense modes backed by the tested split services
- Running net balances with exact zero-sum integer-cent accounting
- Settle Up payments minimizing the number of debtor-to-creditor transactions

For example, splitting Rs. 100.00 among three people produces Rs. 33.34,
Rs. 33.33, and Rs. 33.33 in participant order. The integer-cent shares still
total exactly Rs. 100.00.

Percentage splits must total exactly 100%. Fractional-cent results are floored,
then remaining cents are assigned by largest fractional remainder with participant
order breaking ties. For example, one cent split 50%/50% goes to the first
participant while the second receives zero cents, preserving the one-cent total.

Expense and people data remain in memory for the current application session.
Expense endpoints are available at `/api/expenses`, balances at `/api/balances`,
and derived settlement payments at `/api/settlements`.

Balances are derived from the current people and expenses whenever requested,
so edits and deletions cannot leave stale balance state. Positive balances should
be received, negative balances are owed, and settled balances are zero. The
accounting invariant is `sum(all balances) = Rs. 0.00`.

Settle Up uses integer cents and an exact memoized DFS/backtracking search rather
than treating a greedy result as optimal. Payments always flow from debtor to
creditor. Exact minimum settlement has combinatorial worst-case complexity, so
this implementation is intended for small assessment-sized groups.

## Run

```sh
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```sh
python -m pytest -v
```
