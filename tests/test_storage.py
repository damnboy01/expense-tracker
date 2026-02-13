# tests/test_storage.py
"""Unit tests for the storage module — file I/O for expenses and limits."""

import os
import tempfile
import unittest
from unittest.mock import patch

from src.storage import (
    load_expenses,
    append_expense_row,
    get_weekly_limit,
    set_weekly_limit,
)


class TestExpenseIO(unittest.TestCase):
    """Tests for raw expense CSV read / write."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.tmpdir, "expenses_testuser.csv")
        self.patch_ef = patch("src.storage.expense_file", return_value=self.test_csv)
        self.patch_ef.start()

    def tearDown(self):
        self.patch_ef.stop()
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        os.rmdir(self.tmpdir)

    def test_load_empty(self):
        """Loading when no CSV exists returns empty DataFrame."""
        df = load_expenses("testuser")
        self.assertTrue(df.empty)
        self.assertListEqual(list(df.columns), ["Date", "Amount", "Category", "Note"])

    def test_append_and_load(self):
        """Appending a row then loading it back works."""
        append_expense_row("testuser", "2026-01-15", 150.0, "food", "lunch")
        df = load_expenses("testuser")
        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df.iloc[0]["Amount"], 150.0)

    def test_append_multiple(self):
        """Multiple appends accumulate rows."""
        append_expense_row("testuser", "2026-01-10", 100.0, "food", "a")
        append_expense_row("testuser", "2026-01-11", 200.0, "fuel", "b")
        append_expense_row("testuser", "2026-01-12", 50.0, "food", "c")
        df = load_expenses("testuser")
        self.assertEqual(len(df), 3)
        self.assertAlmostEqual(df["Amount"].sum(), 350.0)


class TestWeeklyLimitIO(unittest.TestCase):
    """Tests for limit file read / write."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.test_limit = os.path.join(self.tmpdir, "limit_testuser.txt")
        self.patch_lf = patch("src.storage.limit_file", return_value=self.test_limit)
        self.patch_lf.start()

    def tearDown(self):
        self.patch_lf.stop()
        if os.path.exists(self.test_limit):
            os.remove(self.test_limit)
        os.rmdir(self.tmpdir)

    def test_default_limit(self):
        """No file on disk returns the default."""
        limit = get_weekly_limit("testuser")
        self.assertEqual(limit, 1000.0)

    def test_set_and_get(self):
        set_weekly_limit("testuser", 5000.0)
        self.assertAlmostEqual(get_weekly_limit("testuser"), 5000.0)


if __name__ == "__main__":
    unittest.main()
