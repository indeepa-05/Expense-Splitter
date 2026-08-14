# Expense Splitter

## Overview

Expense Splitter is a single-session web application for recording shared
expenses and calculating exactly who owes or should receive money. A group can
add people, record who paid, split costs equally or by percentage, edit or
delete expenses, review running balances, and generate a minimum-transaction
settlement plan.

All monetary values are represented internally as integer cents. This keeps
expense shares, balances, and settlements exact.

## Features

- **People:** add people with case-insensitive duplicate-name validation, list
  them in creation order, and remove people who are not referenced by expenses.
- **Expenses:** create, list, retrieve, edit, and delete shared expenses.
- **Split modes:** deterministic Equal Split and Decimal-based Percentage Split.
- **Form conveniences:** Select All participants, live percentage
  Total/Remaining/Over-by feedback, money input normalization, and a clear
  edit/cancel workflow.
- **Accounting:** exact running net balances where positive means to receive and
  negative means owes.
- **Settle Up:** debtor-to-creditor instructions that minimize the number of
  payment transactions.
- **Session control:** in-memory storage plus Start New Session to clear all
  records and reset IDs without restarting the server.

## Technology Stack

- Python 3.11+
- FastAPI and Pydantic
- Uvicorn
- Jinja2
- HTML and CSS
- Vanilla JavaScript
- pytest and HTTPX

No external database or frontend framework is required.

## Project Structure

```text
Expense Splitter/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI routes, templates, and static setup
│   ├── models.py               # API and domain models
│   ├── repository.py           # In-memory people and expense repositories
│   ├── services/
│   │   ├── __init__.py
│   │   ├── money.py            # Exact money parsing and formatting
│   │   ├── splits.py           # Equal and percentage allocation
│   │   ├── expenses.py         # Expense validation and orchestration
│   │   ├── balances.py         # Derived running balances
│   │   └── settlement.py       # Optimal settlement search
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── styles.css
│       └── app.js
├── tests/
│   ├── test_app.py
│   ├── test_people.py
│   ├── test_money.py
│   ├── test_splits.py
│   ├── test_percentages.py
│   ├── test_expenses.py
│   ├── test_balances.py
│   ├── test_settlement.py
│   ├── test_session_management.py
│   ├── test_frontend.py
│   └── test_integration.py
├── run.py
├── start_app.bat
├── requirements.txt
├── PROMPTS.md
└── README.md
```

## Setup

From a fresh clone in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If local PowerShell policy prevents activation, follow your organization's
execution-policy guidance or use the environment's Python directly without
activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Avoid changing machine-wide execution policy solely for this project.

## Running the Application

### Easiest Windows method

After setup, double-click `start_app.bat`. It uses
`.venv\Scripts\python.exe`, starts the server, and opens the default browser.
The virtual environment and dependencies must already be installed.

### Simple terminal method

```powershell
python run.py
```

This starts the application on `127.0.0.1:8000` and opens the default browser.
The launcher intentionally runs without auto-reload so the browser opens once.

### Development method

```powershell
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Auto-reload is useful
while editing source files.

## Using the Application

1. Add everyone sharing costs.
2. Enter an expense description and amount.
3. Choose the payer.
4. Choose Equal Split or Percentage Split.
5. Select participants and, for percentage mode, enter percentages totaling
   exactly 100%.
6. Save the expense and review Expenses, Balances, and Settle Up.
7. Edit or delete expenses when details change.

The payer does not need to be a participant. A person referenced by an expense
cannot be removed until those expense references are edited or deleted. Start
New Session permanently clears the current in-memory people and expenses and
restarts ID counters.

## Running Tests

Run the complete suite with concise output:

```powershell
python -m pytest
```

Show every collected test and result:

```powershell
python -m pytest -v
```

Each file can also run independently:

```powershell
python -m pytest tests/test_app.py -v
python -m pytest tests/test_people.py -v
python -m pytest tests/test_money.py -v
python -m pytest tests/test_splits.py -v
python -m pytest tests/test_percentages.py -v
python -m pytest tests/test_expenses.py -v
python -m pytest tests/test_balances.py -v
python -m pytest tests/test_settlement.py -v
python -m pytest tests/test_session_management.py -v
python -m pytest tests/test_frontend.py -v
python -m pytest tests/test_integration.py -v
```

Run one exact edge case by using its pytest node ID:

```powershell
python -m pytest tests/test_settlement.py::test_optimal_settlement_beats_greedy_counterexample -v
```

This is useful for debugging one feature or demonstrating a specific assessment
requirement during review.

## Test Structure

| Test file | Purpose |
|---|---|
| `test_app.py` | FastAPI root and health checks |
| `test_people.py` | People creation, validation, ordering, and isolation |
| `test_money.py` | Exact money parsing and display formatting |
| `test_splits.py` | Equal splitting and deterministic remainder handling |
| `test_percentages.py` | Decimal percentages and largest-remainder allocation |
| `test_expenses.py` | Expense CRUD and split-service integration |
| `test_balances.py` | Running balances, recalculation, and zero-sum checks |
| `test_settlement.py` | Exact minimum-transaction settlement and API behavior |
| `test_session_management.py` | Safe person removal and complete session reset |
| `test_frontend.py` | Jinja HTML and static-asset smoke checks |
| `test_integration.py` | Complete API workflows and regression invariants |

The suite combines unit, API, integration, rounding-edge, and regression tests.
Important invariants include:

```python
sum(expense.shares.values()) == expense.amount_cents
sum(all_balances.values()) == 0
all(balance == 0 for balance in settled_balances.values())
```

These checks prevent missing cents, created cents, stale balances, and incomplete
settlements.

## Running Balances

Expenses are the accounting source of truth. Balances are recalculated from all
current expenses rather than stored as mutable person state:

```python
balances[payer] += expense.amount_cents

for participant, share in expense.shares.items():
    balances[participant] -= share
```

- Positive balance: the person should receive money.
- Negative balance: the person owes money.
- Zero balance: the person is settled.

Because every expense's shares equal its amount, all balances sum exactly to
zero.

## Money and Rounding

Binary floating-point arithmetic is deliberately avoided for canonical
financial calculations because values such as decimal currency fractions may
not have exact binary representations.

```text
Rs. 100.00 -> 10000 cents
```

Integer cents are used for expense amounts, shares, balances, and settlement
transactions. Monetary strings are parsed with `Decimal` and must be positive
with no more than two decimal places.

### Equal Split

Equal splitting uses integer `divmod`. For Rs. 100.00 split among three people:

```text
Rs. 33.34
Rs. 33.33
Rs. 33.33
```

The remaining cent goes to the first participant in input order, so the result
is deterministic and still totals exactly Rs. 100.00.

### Percentage Split

Percentages are parsed directly with `Decimal`, must be positive, and must total
exactly 100%. Exact fractional-cent shares are floored first; remaining cents
are assigned using the Largest Remainder Method, with participant order breaking
ties deterministically.

The frontend Total/Remaining/Over-by indicator is only a convenience. Python
backend validation and allocation remain authoritative.

## Settle Up Algorithm

Settle Up returns payments from debtors to creditors while minimizing the
number of non-zero transactions. It uses an exact memoized DFS/backtracking
search with opposite-sign pairing, zero-state removal, exact-cancellation
prioritization, and deterministic lexicographic tie-breaking.

A largest-debtor/largest-creditor greedy algorithm can produce a valid plan but
does not always guarantee the global minimum transaction count. Exact search is
therefore used for the normal small group sizes expected by this application.

## Data Storage and Sessions

Persistence is intentionally in memory because this assessment targets one
active session and does not require database infrastructure.

- Restarting the server clears all state.
- Start New Session clears state without restarting and resets both ID counters.
- Deleting one person or expense during a session does not reuse its ID.
- Repository responsibilities are separated from validation and calculation,
  allowing persistent storage to replace the repository later.

## API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Serve the browser interface |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/people` | List people |
| `POST` | `/api/people` | Add a person |
| `DELETE` | `/api/people/{person_id}` | Remove an unused person |
| `GET` | `/api/expenses` | List expenses |
| `POST` | `/api/expenses` | Create an expense |
| `GET` | `/api/expenses/{expense_id}` | Retrieve one expense |
| `PUT` | `/api/expenses/{expense_id}` | Replace/edit an expense |
| `DELETE` | `/api/expenses/{expense_id}` | Delete an expense |
| `GET` | `/api/balances` | Return current net balances |
| `GET` | `/api/settlements` | Return optimal settlement instructions |
| `DELETE` | `/api/session` | Start a fresh in-memory session |

FastAPI also exposes interactive API documentation at `/docs` while the server
is running.

## Design Decisions

- **Integer cents:** eliminate binary floating-point money errors.
- **Decimal percentages:** preserve exact decimal input and exact 100% checks.
- **Expenses as source of truth:** avoid stale mutable balance state after edits
  and deletion.
- **Exact settlement search:** guarantee minimum transaction count rather than
  accepting a potentially suboptimal greedy result.
- **In-memory repositories:** match the assessment's single-session scope
  without unnecessary infrastructure.
- **Backend-authoritative calculations:** JavaScript manages interaction and
  rendering; Python owns financial validation and calculation.

## Assumptions

- Expense amounts and selected percentages are positive.
- Percentage allocations use no more than two decimal places and total exactly
  100%.
- Group sizes are modest enough for exact settlement search.
- A payer may be outside the participant set.
- The application is operated as one shared, trusted local session.

## Limitations

- State does not persist across server restarts.
- There are no user accounts, authentication, or access controls.
- Exact settlement has combinatorial worst-case complexity and targets normal
  small groups.
- The application provides payment instructions but no payment processing.

## Future Improvements

- PostgreSQL, Firestore, or another durable persistence layer
- Named and shareable sessions
- Authentication and authorization
- Exportable reports and expense categories
- Automated browser interaction tests
- Production deployment configuration

## AI Assistance

AI assistance was used during incremental development, documentation, and
review. Detailed task-level usage is recorded in [PROMPTS.md](PROMPTS.md).
Suggestions were reviewed against the automated test suite and manual application
workflows rather than accepted without validation.
