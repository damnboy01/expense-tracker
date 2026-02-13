# tests/test_tracker.py
"""Unit tests for the tracker module — auth and expense business logic."""

import os
import tempfile
import unittest
from unittest.mock import patch

from src.tracker import (
    load_users,
    register_user,
    verify_user,
    add_expense,
    weekly_expense_total,
)
from src.storage import load_expenses


class TestUserAuth(unittest.TestCase):
    """Tests for register / verify flow."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.users_file = os.path.join(self.tmpdir, "users.json")
        # Patch the USERS_FILE constant inside the storage module (where the I/O happens)
        self.patcher = patch("src.storage.USERS_FILE", self.users_file)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.users_file):
            os.remove(self.users_file)
        os.rmdir(self.tmpdir)

    def test_register_creates_user(self):
        ok, msg = register_user("alice", "secret")
        self.assertTrue(ok)
        users = load_users()
        self.assertIn("alice", users)

    def test_register_duplicate_fails(self):
        register_user("bob", "pass1")
        ok, msg = register_user("bob", "pass2")
        self.assertFalse(ok)
        self.assertIn("already exists", msg)

    def test_register_empty_username_fails(self):
        ok, msg = register_user("", "pass")
        self.assertFalse(ok)
        self.assertIn("required", msg.lower())

    def test_verify_correct_password(self):
        register_user("carol", "mypass")
        self.assertTrue(verify_user("carol", "mypass"))

    def test_verify_wrong_password(self):
        register_user("dave", "correct")
        self.assertFalse(verify_user("dave", "wrong"))

    def test_verify_nonexistent_user(self):
        self.assertFalse(verify_user("nobody", "pass"))

    def test_default_guest_account(self):
        """First load auto-creates a guest account with password 1234."""
        users = load_users()
        self.assertIn("guest", users)
        self.assertTrue(verify_user("guest", "1234"))


class TestExpenseOperations(unittest.TestCase):
    """Tests for add_expense and weekly_expense_total."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.tmpdir, "expenses_testuser.csv")
        # Patch expense_file in storage (where both append_expense_row and load_expenses resolve paths)
        self.patch_ef = patch("src.storage.expense_file", return_value=self.test_csv)
        self.patch_ef.start()

    def tearDown(self):
        self.patch_ef.stop()
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        os.rmdir(self.tmpdir)

    def test_add_and_load(self):
        """Adding an expense then loading it back works."""
        add_expense("testuser", 150.0, "food", "lunch", date="2026-01-15")
        df = load_expenses("testuser")
        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df.iloc[0]["Amount"], 150.0)
        self.assertEqual(df.iloc[0]["Category"], "food")

    def test_add_multiple(self):
        """Multiple expenses accumulate."""
        add_expense("testuser", 100.0, "food", "a", date="2026-01-10")
        add_expense("testuser", 200.0, "fuel", "b", date="2026-01-11")
        add_expense("testuser", 50.0, "food", "c", date="2026-01-12")
        df = load_expenses("testuser")
        self.assertEqual(len(df), 3)
        self.assertAlmostEqual(df["Amount"].sum(), 350.0)

    def test_add_with_date_object(self):
        """Passing a datetime.date object works correctly."""
        from datetime import date
        add_expense("testuser", 99.0, "test", "note", date=date(2026, 2, 1))
        df = load_expenses("testuser")
        self.assertEqual(df.iloc[0]["Date"], "2026-02-01")


if __name__ == "__main__":
    unittest.main()
