# Manual integration test checklist

Run `python main.py` and verify each item.

## Authentication

- [ ] Register a new user (username 3+ chars, password 4+ chars)
- [ ] Register fails with duplicate username
- [ ] Login succeeds with correct password
- [ ] Login fails with wrong password

## Transactions

- [ ] Add an income transaction (e.g. Salary $100)
- [ ] Add an expense transaction (e.g. Food $25)
- [ ] Table shows both rows
- [ ] Select a row; form fills with its data
- [ ] Edit a transaction and save; table updates
- [ ] Delete a transaction; table updates
- [ ] Search filters the table (e.g. type "Food")

## Dashboard

- [ ] Balance = total income − total expense (all time)
- [ ] Monthly income/expense match transactions in current month only

## Chart

- [ ] With no expenses this month: shows "No expense data for this month"
- [ ] After adding expenses: pie chart shows categories

## Export

- [ ] Export CSV saves a file
- [ ] CSV opens in Excel/spreadsheet with correct columns and rows

## Edge cases

- [ ] Amount 0 or negative is rejected
- [ ] App does not crash with empty transaction list
