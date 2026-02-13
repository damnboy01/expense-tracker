# tests/test_analytics.py
"""Unit tests for the analytics module."""

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

import pandas as pd

from src.analytics import (
    category_summary,
    detect_recurring,
    spending_change,
    generate_insights,
    ai_answer,
)


def _make_df(rows):
    """Helper: build a DataFrame from (date_str, amount, category, note) tuples."""
    return pd.DataFrame(rows, columns=["Date", "Amount", "Category", "Note"])


class TestCategorySummary(unittest.TestCase):

    def test_empty_data(self):
        empty = pd.DataFrame(columns=["Date", "Amount", "Category", "Note"])
        with patch("src.analytics.load_expenses", return_value=empty):
            result = category_summary("u", period_days=30)
        self.assertTrue(result.empty)

    def test_sums_by_category(self):
        today = datetime.today().strftime("%Y-%m-%d")
        df = _make_df([
            (today, 100.0, "food", "lunch"),
            (today, 200.0, "fuel", "petrol"),
            (today, 50.0, "food", "snack"),
        ])
        with patch("src.analytics.load_expenses", return_value=df):
            result = category_summary("u", period_days=30)
        self.assertAlmostEqual(result["food"], 150.0)
        self.assertAlmostEqual(result["fuel"], 200.0)
        self.assertEqual(result.index[0], "fuel")


class TestDetectRecurring(unittest.TestCase):

    def test_empty(self):
        empty = pd.DataFrame(columns=["Date", "Amount", "Category", "Note"])
        with patch("src.analytics.load_expenses", return_value=empty):
            self.assertEqual(detect_recurring("u"), [])

    def test_finds_recurring(self):
        today = datetime.today().strftime("%Y-%m-%d")
        df = _make_df([
            (today, 10, "sub", "Netflix"),
            (today, 10, "sub", "Netflix"),
            (today, 10, "sub", "Netflix"),
            (today, 50, "food", "lunch"),
        ])
        with patch("src.analytics.load_expenses", return_value=df):
            result = detect_recurring("u", min_occurrences=3)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["note"], "Netflix")
        self.assertEqual(result[0]["count"], 3)


class TestSpendingChange(unittest.TestCase):

    def test_empty(self):
        empty = pd.DataFrame(columns=["Date", "Amount", "Category", "Note"])
        with patch("src.analytics.load_expenses", return_value=empty):
            self.assertEqual(spending_change("u"), {})

    def test_no_previous_period(self):
        today = datetime.today().strftime("%Y-%m-%d")
        df = _make_df([(today, 500, "misc", "x")])
        with patch("src.analytics.load_expenses", return_value=df):
            result = spending_change("u", period_days=7)
        self.assertIsNone(result["percent_change"])

    def test_increase_detected(self):
        today = datetime.today()
        recent = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        old = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        df = _make_df([
            (recent, 1000, "misc", "x"),
            (old, 500, "misc", "y"),
        ])
        with patch("src.analytics.load_expenses", return_value=df):
            result = spending_change("u", period_days=7)
        self.assertIsNotNone(result["percent_change"])
        self.assertGreater(result["percent_change"], 0)


class TestGenerateInsights(unittest.TestCase):

    def test_empty_data_message(self):
        empty = pd.DataFrame(columns=["Date", "Amount", "Category", "Note"])
        with patch("src.analytics.load_expenses", return_value=empty):
            insights = generate_insights("u")
        self.assertEqual(len(insights), 1)
        self.assertIn("No expenses", insights[0])

    def test_returns_list_of_strings(self):
        today = datetime.today().strftime("%Y-%m-%d")
        df = _make_df([(today, 100, "food", "lunch")])
        with patch("src.analytics.load_expenses", return_value=df):
            insights = generate_insights("u")
        self.assertIsInstance(insights, list)
        for item in insights:
            self.assertIsInstance(item, str)


class TestAIAnswer(unittest.TestCase):

    def test_empty_data(self):
        empty = pd.DataFrame(columns=["Date", "Amount", "Category", "Note"])
        with patch("src.analytics.load_expenses", return_value=empty):
            result = ai_answer("u", "Where am I overspending?")
        self.assertIn("No expenses", result)

    def test_fallback_message(self):
        today = datetime.today().strftime("%Y-%m-%d")
        df = _make_df([(today, 100, "food", "lunch")])
        with patch("src.analytics.load_expenses", return_value=df):
            result = ai_answer("u", "random gibberish question")
        self.assertIn("Sorry", result)


if __name__ == "__main__":
    unittest.main()
