# src/storage.py
# Data persistence — file paths, directory setup, and all raw I/O operations.

import os
import json
import csv

import pandas as pd

# --------------- Directory Paths ---------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# Ensure runtime directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# --------------- File Path Helpers ---------------
USERS_FILE = os.path.join(DATA_DIR, "users.json")

DEFAULT_WEEKLY_LIMIT = 1000.0


def expense_file(username: str) -> str:
    """Return the CSV path for a given user's expenses."""
    return os.path.join(DATA_DIR, f"expenses_{username}.csv")


def limit_file(username: str) -> str:
    """Return the text file path for a given user's weekly limit."""
    return os.path.join(DATA_DIR, f"limit_{username}.txt")


# --------------- User Storage ---------------

def load_users_raw() -> dict:
    """Read the users JSON file.  Returns empty dict when the file is absent."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users: dict):
    """Persist the users dictionary to disk."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# --------------- Expense Storage ---------------

def load_expenses(username: str) -> pd.DataFrame:
    """Load all expenses for a user as a DataFrame."""
    path = expense_file(username)
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame(columns=["Date", "Amount", "Category", "Note"])
    return pd.DataFrame(columns=["Date", "Amount", "Category", "Note"])


def append_expense_row(username: str, date_str: str, amount: float, category: str, note: str):
    """Append a single expense row to the user's CSV file."""
    path = expense_file(username)
    exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if (not exists) or (os.path.getsize(path) == 0):
            w.writerow(["Date", "Amount", "Category", "Note"])
        w.writerow([date_str, float(amount), category, note])


def save_expenses_df(username: str, df: pd.DataFrame):
    """Overwrite the expense CSV with a DataFrame (used for CSV import merge)."""
    path = expense_file(username)
    df.to_csv(path, index=False)


# --------------- Limit Storage ---------------

def get_weekly_limit(username: str) -> float:
    """Read the user's weekly spending limit (or return default)."""
    path = limit_file(username)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return float(f.read())
        except Exception:
            return DEFAULT_WEEKLY_LIMIT
    return DEFAULT_WEEKLY_LIMIT


def set_weekly_limit(username: str, limit: float):
    """Persist a new weekly spending limit for the user."""
    path = limit_file(username)
    with open(path, "w") as f:
        f.write(str(limit))
