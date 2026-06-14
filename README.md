# Expense Tracker MVP (Student Edition)

A simple desktop expense tracker built with Python, PyQt5, and SQLite.

## Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

On first run, the app creates `expense.db` in this folder. Do not commit real user data to Git.

## Team file ownership

| Member | Files |
|--------|-------|
| 1 — UI | `ui/login_window.py` |
| 2 — Database | `database/db.py` |
| 3 — Transactions | `ui/main_window.py` (form + table) |
| 4 — Dashboard + chart | `ui/main_window.py` (summary), `ui/chart_widget.py` |
| 5 — Integration | `main.py`, `requirements.txt`, `README.md`, CSV export, tests |

## Definition of done

- [ ] New user can register and log in
- [ ] User can add, edit, and delete income and expense transactions
- [ ] Dashboard shows balance and current-month income/expense
- [ ] Pie chart shows expense categories for the current month
- [ ] Export CSV contains all transactions for the logged-in user
- [ ] App handles empty data and invalid input without crashing

## Known limitations (MVP)

- Local database only (no cloud sync)
- English UI only
- One pie chart (no line charts or Excel export)
- Categories are fixed in code
- Passwords are hashed locally but this is a learning project, not production security

## Manual testing

See [TEST_CHECKLIST.md](TEST_CHECKLIST.md) for step-by-step integration tests.

## Automated tests

```bash
python -m unittest tests.test_db -v
```
