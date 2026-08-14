# Expense Splitter

## Project Description

**Expense Splitter** is a single-session web application that helps a group
record shared costs in Sri Lankan Rupees (LKR), calculate how much each person
owes or should receive, and settle all balances using the minimum number of
payment transactions.

A typical group may have one person pay for dinner, another pay for
accommodation, and another pay for transport. Expense Splitter combines those
payments and shows how to settle the group fairly. It supports adding people,
Equal and Percentage splits, expense editing and deletion, removal of unused
people, running balances, optimized settlement instructions, and starting a
fresh session.

Financial correctness is the central design goal. Money is represented as
integer cents, percentages use exact decimal arithmetic, and every rounding rule
preserves the original total.

## Features

### People Management

- Add people by name; surrounding whitespace is removed.
- Reject duplicate names case-insensitively.
- Remove people who are not referenced by an existing expense.
- Support an unlimited practical number of people for normal use, although the
  exact settlement search is designed for ordinary small groups.

### Expense Management

- Create, list, retrieve, edit, and delete expenses.
- Choose who paid for each expense.
- Keep payer and participant selection independent: the payer does not have to
  be included in the split.
- Recalculate shares, balances, and settlements automatically after edits or
  deletion.

### Split Types

- **Equal Split:** divide integer cents as evenly as possible.
- **Percentage Split:** allocate by Decimal percentages totaling exactly 100%.
- Switch clearly between both modes in the web interface.

### UI Convenience

- Select All control for Equal and Percentage participants.
- Money display normalization such as `12000` to `12000.00` on leaving the
  amount field.
- Live percentage Total, Remaining, and Over-by indicators.
- Edit, Save Changes, Cancel, and Delete expense workflow.
- Start New Session with destructive-action confirmation.

### Accounting

- Exact running net balances.
- Positive balance means the person should receive money.
- Negative balance means the person owes money.
- Zero means settled.
- All group balances sum exactly to zero.

### Settlement

- Minimum-transaction Settle Up calculation.
- Readable instructions such as `Bob pays Carol Rs. 7,000.00`.
- Deterministic results when more than one optimal plan exists.

## Technology Stack

- Python 3.11+
- FastAPI
- Pydantic
- Jinja2
- HTML
- CSS
- Vanilla JavaScript
- Uvicorn
- pytest and HTTPX

No frontend framework or external database is required. The in-memory
repository keeps the assessment focused on exact split, accounting, and
settlement logic rather than unnecessary infrastructure.

## How to Run It

### Step 1 — Install the prerequisites

You need:

- Python 3.11 or later
- Git
- A modern web browser

Check that Python and Git are available:

```powershell
python --version
git --version
```

If both commands print version numbers, they are installed.

### Step 2 — Clone the GitHub repository

```powershell
git clone https://github.com/indeepa-05/Expense-Splitter.git
cd Expense-Splitter
```

### Step 3 — Create a virtual environment

```powershell
python -m venv .venv
```

A virtual environment creates an isolated Python environment for this project,
so its packages do not interfere with other Python projects.

### Step 4 — Activate the virtual environment

#### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Successful activation normally changes the prompt to something similar to
`(.venv) PS ...`.

#### Windows Command Prompt

```cmd
.venv\Scripts\activate.bat
```

If PowerShell policy prevents activation, the environment can still be used
directly without changing unsafe system-wide policy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 5 — Install the requirements

```powershell
python -m pip install -r requirements.txt
```

This installs FastAPI, Pydantic, Uvicorn, Jinja2, pytest, HTTPX, and their
required dependencies.

### Step 6 — Optionally verify the installation

```powershell
python -m pytest -v
```

The complete test suite should pass before demonstration or further changes.

### Step 7 — Use the recommended startup method

The easiest terminal command is:

```powershell
python run.py
```

`run.py` starts FastAPI at
[http://127.0.0.1:8000](http://127.0.0.1:8000) and attempts to open the default
browser automatically. If no browser opens, visit that address manually.

### Step 8 — Use the Windows double-click method

After `.venv` exists and the requirements are installed, Windows users can
double-click `start_app.bat`. The batch file:

1. Changes safely to the project directory.
2. Checks for `.venv\Scripts\python.exe`.
3. Shows setup guidance if the virtual environment is missing.
4. Runs `run.py` with the virtual environment's Python.

### Step 9 — Troubleshoot startup

If `run.py` does not work, try the normal development command:

```powershell
uvicorn app.main:app --reload
```

If `uvicorn` is not recognized as a standalone command, run it through Python:

```powershell
python -m uvicorn app.main:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000). The `--reload`
option is useful during development because the server restarts when source
files change.

### Step 10 — Stop the server

Press `Ctrl+C` in the terminal where the server is running.

### Quick Start

```powershell
git clone https://github.com/indeepa-05/Expense-Splitter.git
cd Expense-Splitter

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pytest -v
python run.py
```

Fallback startup command:

```powershell
python -m uvicorn app.main:app --reload
```

## User Guide

### Step 1 — Add people

Add everyone participating in the group, for example:

```text
Alice
Bob
Carol
Dave
```

Names are trimmed and duplicates are rejected case-insensitively. An unused
person can be removed. A person already referenced as an expense payer or
participant cannot be removed until the relevant expenses are edited or
deleted.

### Step 2 — Add an expense

Complete the Description, Amount, and Paid by fields:

```text
Description: Dinner
Amount: 12000
Paid by: Alice
```

When the amount field loses focus, a valid `12000` is displayed as `12000.00`.
The Python backend still performs the authoritative amount validation.

### Step 3 — Choose a split type

Use the visible switch between Equal and Percentage.

#### Equal Split

Select participants with the checkboxes or use Select All. The payer remains
independent and is not automatically included.

For example, Rs. 12,000.00 split among Alice, Bob, Carol, and Dave produces
Rs. 3,000.00 each.

If an amount does not divide evenly, remainder cents are assigned
deterministically in participant order:

```text
Rs. 100.00 / 3

Rs. 33.34
Rs. 33.33
Rs. 33.33
```

The shares still total exactly Rs. 100.00.

#### Percentage Split

Select each participant and enter their percentage. Selected percentages must
total exactly 100%:

```text
Alice 33.33%
Bob   33.33%
Dave  33.34%
```

The form shows:

```text
Total: 100.00%
Remaining: 0.00%
```

Below 100%, it shows Remaining. Above 100%, it shows Over by. These indicators
are convenience feedback; backend Decimal validation remains authoritative.

### Step 4 — Save the expense

Submit the form. The saved record appears in Expenses with its payer, split
mode, participants, and exact shares.

### Step 5 — Edit or delete expenses

- **Edit** loads the expense into the form.
- Amount, payer, participants, split type, and percentages can all be changed.
- **Save Changes** replaces the expense with fully recalculated shares.
- **Cancel** exits editing without changing the expense.
- **Delete** removes the expense after confirmation.

Balances and settlement instructions automatically recalculate from the current
expense records.

### Step 6 — View running balances

```text
Positive balance = To receive
Negative balance = Owes
Zero balance     = Settled
```

Example:

```text
Alice   + Rs. 5,667.00   To receive
Bob     - Rs. 9,333.00   Owes
Carol   + Rs. 7,000.00   To receive
Dave    - Rs. 3,334.00   Owes
```

### Step 7 — Settle up

Settle Up produces a minimum-transaction payment plan, for example:

```text
Bob pays Carol Rs. 7,000.00
Dave pays Alice Rs. 3,334.00
Bob pays Alice Rs. 2,333.00
```

These are instructions only; the application does not transfer real money.
Following every instruction brings all balances to zero.

### Step 8 — Remove a person

An unused person can be removed after confirmation. If a person is referenced
by an expense, edit or delete that expense first. The application never silently
rewrites historical expenses to remove someone.

### Step 9 — Start a new session

Start New Session asks for confirmation and then clears all people, expenses,
balances, settlement results, edit state, and ID counters. Because storage is
in memory, restarting the server also clears all data.

## Running the Tests

### Run all tests

Verbose output shows every collected test name and result:

```powershell
python -m pytest -v
```

For shorter output:

```powershell
python -m pytest
```

### Run one test file

Every current test module can run independently:

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

### Run one specific test

The optimality regression test exists at this exact pytest node ID:

```powershell
python -m pytest tests/test_settlement.py::test_optimal_settlement_beats_greedy_counterexample -v
```

Running one test is useful when debugging a feature or demonstrating one
assessment requirement during review.

## Test Structure

| Test file | What it verifies |
|---|---|
| `test_app.py` | FastAPI root and health endpoint |
| `test_people.py` | People creation, trimming, duplicates, ordering, and isolation |
| `test_money.py` | Exact money parsing and display formatting |
| `test_splits.py` | Equal splitting and deterministic remainder handling |
| `test_percentages.py` | Percentage validation and largest-remainder allocation |
| `test_expenses.py` | Expense CRUD, validation, mode switching, and split integration |
| `test_balances.py` | Running balances, edits/deletion recalculation, and zero-sum accounting |
| `test_settlement.py` | Exact minimum-transaction settlement and deterministic direction |
| `test_session_management.py` | Safe people removal and full session reset |
| `test_frontend.py` | Jinja page, required UI controls, CSS, and JavaScript smoke checks |
| `test_integration.py` | Complete API workflows, regression cases, and end-to-end invariants |

The suite combines unit, API, integration, rounding-edge, invariant, and
regression tests. Important protections include:

```python
sum(expense.shares.values()) == expense.amount_cents
sum(balances.values()) == 0
all(balance == 0 for balance in final_balances.values())
```

These invariants prevent missing cents, created cents, stale accounting state,
and incomplete settlements.

## Assumptions Made and Why

### Single Session

**Assumption:** The application serves one active local group session rather
than multiple authenticated users.

**Why:** The assignment does not require login or accounts and describes a
single-session tool. This keeps the implementation focused on expense logic.

### In-Memory Persistence

**Assumption:** People and expenses are stored in memory.

**Why:** The assignment explicitly permits in-memory storage and prioritizes
split and settlement correctness over infrastructure. Repository separation
still leaves a clear path to persistent storage later.

### Single Currency

**Assumption:** Every amount uses Sri Lankan Rupees (LKR).

**Why:** The assignment specifies one currency, avoiding exchange-rate and
multi-currency accounting complexity.

### Two Split Modes

**Assumption:** Percentage was selected as the required secondary split mode,
alongside Equal Split.

**Why:** The brief allows Percentage or Exact Amount. Percentage provides a
useful proportional allocation while exercising exact decimal rounding.

### Percentage Validation

**Assumption:** Selected percentages must be positive and total exactly 100%.

**Why:** This prevents under-allocation and over-allocation and protects exact
zero-sum accounting.

### Payer Can Be Outside the Split

**Assumption:** The payer does not have to receive a participant share.

**Why:** Someone may pay on behalf of other people. Keeping payer and participant
roles separate models that real-world case correctly.

### People Removal

**Assumption:** A person referenced by an expense cannot be deleted.

**Why:** Deletion would otherwise create dangling historical references or
silently require rewriting old expenses.

### Equal Split Remainders

**Assumption:** Extra cents are assigned in participant input order.

**Why:** A stable ordering makes totals exact, results repeatable, and edits
deterministic.

### Small Groups for Optimal Settlement

**Assumption:** Normal group sizes are relatively small.

**Why:** Exact minimum-transaction settlement uses DFS/backtracking and has
combinatorial worst-case complexity. This is reasonable for the assessment's
typical group-expense scenario.

## Technical / Design Decisions

### Integer Cents

Canonical money never uses binary floating point:

```text
Rs. 100.00 -> 10000 cents
```

Expense amounts, shares, balances, and settlement payments all use integer
cents. This removes common currency representation and rounding errors.

### Decimal Percentages

Percentage strings are parsed directly with Python `Decimal`, never through a
float. Inputs support up to two decimal places and totals are compared to
exactly `Decimal("100")` without tolerance.

### Equal Split Rounding

Equal splitting uses integer `divmod`. Everyone receives the base share, then
remaining one-cent units go to participants in input order. Rs. 100.00 divided
among three people therefore becomes Rs. 33.34, Rs. 33.33, and Rs. 33.33.

### Largest Remainder Method

Percentage calculations may produce fractional cents. The backend floors each
exact share, ranks the fractional remainders, and distributes missing cents to
the largest remainders. Participant order breaks equal-remainder ties. Final
integer-cent shares always equal the expense total.

### Expenses as the Source of Truth

Balances are derived whenever requested rather than stored as mutable fields:

```python
balances[payer] += expense.amount_cents

for participant, share in expense.shares.items():
    balances[participant] -= share
```

This prevents stale balances after amount, payer, participant, mode, or deletion
changes.

### Zero-Sum Accounting

Every stored expense satisfies:

```python
sum(expense.shares.values()) == expense.amount_cents
```

Therefore the complete accounting system must satisfy:

```python
sum(balances.values()) == 0
```

The services fail loudly on corrupted data instead of silently adjusting a
person's balance.

### Minimum-Transaction Settlement

Settle Up uses exact memoized DFS/backtracking with pruning, opposite-sign
pairing, exact-cancellation prioritization, and deterministic lexicographic
tie-breaking. A largest-debtor/largest-creditor greedy method was not used as
the final algorithm because it can produce a valid plan without guaranteeing
the globally minimum number of transactions.

### Backend-Authoritative Logic

JavaScript manages form state, visibility, convenience formatting, and
rendering. Python remains authoritative for money parsing, percentages, shares,
balances, validation, and settlement. UI arithmetic cannot change canonical
financial results.

### Repository and Session Design

Repositories isolate persistence from business services. Deleting one person
or expense does not reuse its ID during a session. Start New Session resets both
repositories and ID counters. This design can later replace in-memory storage
without rewriting the financial algorithms.

## Anything I Would Do Differently or Build Next With More Time

The next work would be prioritized rather than treated as an unbounded feature
list:

1. **Persistent storage:** replace the in-memory repositories with SQLite for a
   lightweight deployment or PostgreSQL/Firestore for durable shared data. The
   repository/service separation limits the required financial-logic changes.
2. **Shareable sessions:** generate session IDs and URLs so independent groups
   can save and revisit their own expenses.
3. **Authentication:** optionally add accounts for users who need private saved
   history. This was deliberately excluded from the current scope.
4. **Deployment:** package and deploy the Python application to a suitable host
   with persistent storage. Vercel or another Python-capable platform could be
   evaluated based on runtime needs.
5. **Automated browser testing:** use Playwright or Selenium for full form,
   editing, removal, reset, and responsive-layout workflows.
6. **Exports and categories:** support CSV/PDF reports plus categories such as
   Food, Accommodation, Transport, and Activities.
7. **Large-group settlement performance:** investigate stronger bounds or
   alternative exact optimization techniques for unusually large groups.
8. **UI polish:** deepen accessibility review, keyboard behavior, responsive
   layout coverage, and visual feedback.

## Anything Left Incomplete and Why I Prioritized This Way

All core requirements from the brief were implemented, including people
management, expense CRUD, Equal and Percentage splits, exact rounding, running
balances, editing and deletion, optimized minimum-transaction settlement, and
a usable browser interface.

The following non-core capabilities were intentionally left out:

### Persistent Database

Not implemented because the brief explicitly allows in-memory persistence and
encourages prioritizing split and settlement correctness over infrastructure.

### Authentication and User Accounts

Not implemented because login and accounts are outside the required
single-session scope.

### Real Payment Processing

Not implemented because Settle Up calculates instructions; it is not intended
to transfer funds or integrate with banks.

### Production Hosting

No production deployment configuration is included. Local correctness,
portable setup, and submission requirements were prioritized first.

### Extensive Browser Automation

The project includes API integration tests and frontend/static smoke tests, but
not a full Playwright or Selenium suite. Time was directed toward financial
correctness, API integration, rounding invariants, and settlement optimality.

The implementation priority was:

1. Financial correctness
2. Rounding correctness
3. Settlement correctness
4. CRUD and integration behavior
5. Usable UI
6. Infrastructure and polish

This follows the assessment's instruction to prioritize correct split and
settle-up behavior over nonessential infrastructure and visual refinement.

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
| `PUT` | `/api/expenses/{expense_id}` | Edit/replace an expense |
| `DELETE` | `/api/expenses/{expense_id}` | Delete an expense |
| `GET` | `/api/balances` | Return derived current balances |
| `GET` | `/api/settlements` | Return optimal settlement instructions |
| `DELETE` | `/api/session` | Clear data and start a fresh session |

FastAPI's interactive API documentation is available at `/docs` while the
application is running.

## Project Structure

```text
Expense-Splitter/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Routes and web integration
│   ├── models.py               # Request, response, and domain models
│   ├── repository.py           # In-memory repositories
│   ├── services/
│   │   ├── __init__.py
│   │   ├── money.py            # Money parsing and formatting
│   │   ├── splits.py           # Equal and percentage splitting
│   │   ├── expenses.py         # Expense orchestration
│   │   ├── balances.py         # Running balance derivation
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

## AI Assistance

AI assistance was permitted by the assessment and used during incremental
development, testing support, documentation, and review. The task-level prompt
history is recorded transparently in [PROMPTS.md](PROMPTS.md).

AI-assisted suggestions did not replace verification or human review. Changes
were evaluated through the automated pytest suite and manual application
workflows.
