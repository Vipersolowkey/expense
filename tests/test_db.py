"""Tests for database layer."""

import os
import tempfile
import unittest
from datetime import date

from database.db import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.db.init_db()

    def tearDown(self) -> None:
        self.db.close()
        os.unlink(self.tmp.name)

    def test_register_and_login(self) -> None:
        ok, _ = self.db.register_user("alice", "secret")
        self.assertTrue(ok)
        user_id = self.db.login_user("alice", "secret")
        self.assertIsNotNone(user_id)
        self.assertIsNone(self.db.login_user("alice", "wrong"))

    def test_duplicate_username(self) -> None:
        self.db.register_user("bob", "pass1")
        ok, msg = self.db.register_user("bob", "pass2")
        self.assertFalse(ok)
        self.assertIn("exists", msg.lower())

    def test_transaction_crud_and_summary(self) -> None:
        ok, _ = self.db.register_user("carol", "pass")
        user_id = self.db.login_user("carol", "pass")
        assert user_id is not None

        today = date.today().isoformat()
        self.db.add_transaction(
            user_id, "income", "Salary", 1000.0, "paycheck", today
        )
        self.db.add_transaction(
            user_id, "expense", "Food", 50.0, "lunch", today
        )

        txs = self.db.get_transactions(user_id)
        self.assertEqual(len(txs), 2)

        tx_id = txs[0].id
        self.db.update_transaction(
            tx_id, user_id, "expense", "Food", 60.0, "lunch updated", today
        )
        updated = self.db.get_transaction(tx_id, user_id)
        assert updated is not None
        self.assertEqual(updated.amount, 60.0)

        y, m = date.today().year, date.today().month
        summary = self.db.get_summary(user_id, y, m)
        self.assertEqual(summary.monthly_income, 1000.0)
        self.assertEqual(summary.monthly_expense, 60.0)
        self.assertEqual(summary.balance, 940.0)

        totals = self.db.get_category_totals(user_id, y, m)
        self.assertEqual(totals.get("Food"), 60.0)

        self.db.delete_transaction(tx_id, user_id)
        self.assertEqual(len(self.db.get_transactions(user_id)), 1)

    def test_invalid_amount(self) -> None:
        ok, _ = self.db.register_user("dave", "pass")
        user_id = self.db.login_user("dave", "pass")
        assert user_id is not None
        ok, msg = self.db.add_transaction(
            user_id, "expense", "Food", 0, "", date.today().isoformat()
        )
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
