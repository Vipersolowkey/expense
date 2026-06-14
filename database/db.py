"""SQLite database layer for Expense Tracker MVP."""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any

DB_FILENAME = "expense.db"
PBKDF2_ITERATIONS = 100_000

INCOME_CATEGORIES = ("Salary", "Allowance", "Loan", "Other")
EXPENSE_CATEGORIES = ("Food", "Transport", "Education", "Entertainment", "Loan", "Other")
TRANSACTION_TYPES = ("income", "expense")


@dataclass
class Transaction:
    id: int
    user_id: int
    type: str
    category: str
    amount: float
    note: str
    date: str


@dataclass
class Summary:
    balance: float
    monthly_income: float
    monthly_expense: float


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, DB_FILENAME)
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def init_db(self) -> None:
        conn = self.connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                note TEXT NOT NULL DEFAULT '',
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_user_date
                ON transactions(user_id, date);
            """
        )
        conn.commit()

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS,
        )
        return f"{salt}${digest.hex()}"

    def _verify_password(self, password: str, stored: str) -> bool:
        try:
            salt, digest_hex = stored.split("$", 1)
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS,
        )
        return secrets.compare_digest(digest.hex(), digest_hex)

    def register_user(self, username: str, password: str) -> tuple[bool, str]:
        username = username.strip()
        if len(username) < 3:
            return False, "Username must be at least 3 characters."
        if len(password) < 4:
            return False, "Password must be at least 4 characters."

        conn = self.connect()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, self._hash_password(password)),
            )
            conn.commit()
            return True, "Registration successful."
        except sqlite3.IntegrityError:
            return False, "Username already exists."

    def login_user(self, username: str, password: str) -> int | None:
        conn = self.connect()
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
        if row is None:
            return None
        if not self._verify_password(password, row["password_hash"]):
            return None
        return int(row["id"])

    def add_transaction(
        self,
        user_id: int,
        tx_type: str,
        category: str,
        amount: float,
        note: str,
        tx_date: str,
    ) -> tuple[bool, str]:
        err = self._validate_transaction(tx_type, category, amount, tx_date)
        if err:
            return False, err

        conn = self.connect()
        conn.execute(
            """
            INSERT INTO transactions (user_id, type, category, amount, note, date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, tx_type, category, amount, note.strip(), tx_date),
        )
        conn.commit()
        return True, "Transaction added."

    def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        tx_type: str,
        category: str,
        amount: float,
        note: str,
        tx_date: str,
    ) -> tuple[bool, str]:
        err = self._validate_transaction(tx_type, category, amount, tx_date)
        if err:
            return False, err

        conn = self.connect()
        cur = conn.execute(
            """
            UPDATE transactions
            SET type = ?, category = ?, amount = ?, note = ?, date = ?
            WHERE id = ? AND user_id = ?
            """,
            (tx_type, category, amount, note.strip(), tx_date, transaction_id, user_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return False, "Transaction not found."
        return True, "Transaction updated."

    def delete_transaction(self, transaction_id: int, user_id: int) -> tuple[bool, str]:
        conn = self.connect()
        cur = conn.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, user_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return False, "Transaction not found."
        return True, "Transaction deleted."

    def get_transactions(
        self,
        user_id: int,
        search: str | None = None,
    ) -> list[Transaction]:
        conn = self.connect()
        query = """
            SELECT id, user_id, type, category, amount, note, date
            FROM transactions
            WHERE user_id = ?
        """
        params: list[Any] = [user_id]

        if search and search.strip():
            term = f"%{search.strip()}%"
            query += """
                AND (
                    category LIKE ? OR note LIKE ? OR type LIKE ? OR date LIKE ?
                )
            """
            params.extend([term, term, term, term])

        query += " ORDER BY date DESC, id DESC"
        rows = conn.execute(query, params).fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def get_transaction(self, transaction_id: int, user_id: int) -> Transaction | None:
        conn = self.connect()
        row = conn.execute(
            """
            SELECT id, user_id, type, category, amount, note, date
            FROM transactions
            WHERE id = ? AND user_id = ?
            """,
            (transaction_id, user_id),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_transaction(row)

    def get_summary(self, user_id: int, year: int, month: int) -> Summary:
        conn = self.connect()
        prefix = f"{year:04d}-{month:02d}"

        total_income = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = ? AND type = 'income'
            """,
            (user_id,),
        ).fetchone()[0]

        total_expense = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = ? AND type = 'expense'
            """,
            (user_id,),
        ).fetchone()[0]

        monthly_income = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = ? AND type = 'income' AND date LIKE ?
            """,
            (user_id, f"{prefix}%"),
        ).fetchone()[0]

        monthly_expense = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = ? AND type = 'expense' AND date LIKE ?
            """,
            (user_id, f"{prefix}%"),
        ).fetchone()[0]

        return Summary(
            balance=float(total_income) - float(total_expense),
            monthly_income=float(monthly_income),
            monthly_expense=float(monthly_expense),
        )

    def get_category_totals(
        self, user_id: int, year: int, month: int
    ) -> dict[str, float]:
        conn = self.connect()
        prefix = f"{year:04d}-{month:02d}"
        rows = conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE user_id = ? AND type = 'expense' AND date LIKE ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id, f"{prefix}%"),
        ).fetchall()
        return {row["category"]: float(row["total"]) for row in rows}

    def _validate_transaction(
        self, tx_type: str, category: str, amount: float, tx_date: str
    ) -> str | None:
        if tx_type not in TRANSACTION_TYPES:
            return "Invalid transaction type."
        valid_categories = (
            INCOME_CATEGORIES if tx_type == "income" else EXPENSE_CATEGORIES
        )
        if category not in valid_categories:
            return "Invalid category for this type."
        if amount <= 0:
            return "Amount must be greater than zero."
        try:
            date.fromisoformat(tx_date)
        except ValueError:
            return "Invalid date format."
        return None

    @staticmethod
    def _row_to_transaction(row: sqlite3.Row) -> Transaction:
        return Transaction(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            type=str(row["type"]),
            category=str(row["category"]),
            amount=float(row["amount"]),
            note=str(row["note"]),
            date=str(row["date"]),
        )
