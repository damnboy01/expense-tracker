# src/tracker.py
# Core business logic — user auth, expense operations, and payment integration.

import os
import secrets
import datetime as _dt
from datetime import datetime, timedelta

import pandas as pd

from src.storage import (
    load_users_raw,
    save_users,
    load_expenses,
    append_expense_row,
)
from src.utils import hash_with_salt


# =====================================================================
# User authentication
# =====================================================================

def load_users() -> dict:
    """Load all users, auto-creating a default guest account if the file is empty."""
    users = load_users_raw()
    if not users:
        salt = secrets.token_hex(8)
        pw_hash = hash_with_salt("1234", salt)
        users = {"guest": {"salt": salt, "pw_hash": pw_hash}}
        save_users(users)
    return users


def register_user(username: str, password: str) -> tuple:
    """Register a new user. Returns (success: bool, message: str)."""
    users = load_users()
    username = username.strip()
    if not username:
        return False, "Username required."
    if username in users:
        return False, "Username already exists."
    salt = secrets.token_hex(8)
    pw_hash = hash_with_salt(password, salt)
    users[username] = {"salt": salt, "pw_hash": pw_hash}
    save_users(users)
    return True, "Registered."


def verify_user(username: str, password: str) -> bool:
    """Verify a username / password combination."""
    users = load_users()
    if username not in users:
        return False
    salt = users[username]["salt"]
    return users[username]["pw_hash"] == hash_with_salt(password, salt)


# =====================================================================
# Expense operations
# =====================================================================

def add_expense(username: str, amount: float, category: str, note: str, date=None):
    """Resolve the date then persist the expense via storage."""
    # Handles datetime.date, datetime.datetime, str, or None
    if isinstance(date, _dt.date):
        date_str = date.strftime("%Y-%m-%d")
    elif isinstance(date, str) and date:
        date_str = date
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

    append_expense_row(username, date_str, amount, category, note)


def weekly_expense_total(username: str) -> float:
    """Sum of expenses in the last 7 days."""
    df = load_expenses(username)
    if df.empty:
        return 0.0
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    week_ago = datetime.today() - timedelta(days=7)
    return df[df["Date"] >= week_ago]["Amount"].sum()


# =====================================================================
# Razorpay payment integration (test mode)
# =====================================================================

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_RSrYrIik3LfPzl")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "tOrAIpnwpns10tG2YHy2Q5TK")

try:
    import razorpay
except ImportError:
    razorpay = None


def get_razorpay_client():
    """Return a configured Razorpay client, or None if unavailable."""
    if razorpay is None:
        return None
    try:
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        return None


def create_order(client, amount_inr: float) -> dict:
    """Create a Razorpay test order. Raises on failure."""
    if client is None:
        raise Exception("Razorpay client not configured or package missing.")
    return client.order.create({
        "amount": int(amount_inr * 100),
        "currency": "INR",
        "payment_capture": 1,
    })
