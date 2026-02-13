# src/analytics.py
# Analytics computations, auto-insights, AI assistant, and chart export.

import os
from datetime import datetime, timedelta

import pandas as pd

from src.storage import load_expenses, REPORTS_DIR


# =====================================================================
# Time series
# =====================================================================

def get_time_series(username: str, freq: str = "D", months: int = 3) -> pd.Series:
    """Daily (or other freq) spending totals for the last N months."""
    df = load_expenses(username)
    if df.empty:
        return pd.Series(dtype=float)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    start = datetime.today() - pd.DateOffset(months=months)
    df = df[df["Date"] >= start]
    return df.set_index("Date").resample(freq)["Amount"].sum().fillna(0)


# =====================================================================
# Category breakdown
# =====================================================================

def category_summary(username: str, period_days: int = 30) -> pd.Series:
    """Total spending per category over the last N days."""
    df = load_expenses(username)
    if df.empty:
        return pd.Series(dtype=float)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    since = datetime.today() - timedelta(days=period_days)
    df = df[df["Date"] >= since]
    return df.groupby("Category")["Amount"].sum().sort_values(ascending=False)


def daily_heatmap(username: str, days: int = 30):
    """Spending totals by day of the week."""
    df = load_expenses(username)
    if df.empty:
        return None
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    since = datetime.today() - timedelta(days=days)
    df = df[df["Date"] >= since]
    return (
        df.groupby(df["Date"].dt.day_name())["Amount"]
        .sum()
        .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        .fillna(0)
    )


# =====================================================================
# Recurring charges
# =====================================================================

def detect_recurring(username: str, min_occurrences: int = 3, window_days: int = 90) -> list:
    """Find notes that appear at least *min_occurrences* times."""
    df = load_expenses(username)
    if df.empty:
        return []
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    since = datetime.today() - timedelta(days=window_days)
    df = df[df["Date"] >= since]
    candidates = df.groupby("Note")["Amount"].agg(["count", "mean"]).sort_values("count", ascending=False)
    recurring = []
    for idx, row in candidates.iterrows():
        if row["count"] >= min_occurrences:
            recurring.append({"note": idx, "count": int(row["count"]), "avg": float(row["mean"])})
    return recurring


# =====================================================================
# Spending change (period-over-period)
# =====================================================================

def spending_change(username: str, period_days: int = 7) -> dict:
    """Compare recent period spending to the previous period."""
    df = load_expenses(username)
    if df.empty:
        return {}
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    end = datetime.today()
    start = end - timedelta(days=period_days)
    prev_start = start - timedelta(days=period_days)
    recent_sum = df[(df["Date"] >= start) & (df["Date"] < end)]["Amount"].sum()
    prev_sum = df[(df["Date"] >= prev_start) & (df["Date"] < prev_start + timedelta(days=period_days))]["Amount"].sum()
    change = None if prev_sum == 0 else ((recent_sum - prev_sum) / prev_sum) * 100
    return {"recent": float(recent_sum), "previous": float(prev_sum), "percent_change": change}


# =====================================================================
# Auto insights
# =====================================================================

def generate_insights(username: str) -> list:
    """Return a list of plain-text insight strings."""
    insights = []
    df = load_expenses(username)
    if df.empty:
        insights.append("No expenses recorded yet. Add some expenses or upload a bank CSV to get insights.")
        return insights

    top_cats = category_summary(username, 30)
    if not top_cats.empty:
        top = top_cats.index[0]
        pct = (top_cats.iloc[0] / top_cats.sum()) * 100 if top_cats.sum() > 0 else 0
        insights.append(
            f"In the last 30 days, your top category is **{top}** "
            f"accounting for **{pct:.0f}%** of your spending."
        )

    sc = spending_change(username, 7)
    if sc:
        if sc["percent_change"] is None:
            insights.append(f"Your spending last 7 days: ₹{sc['recent']:.2f}. No previous period to compare.")
        elif sc["percent_change"] > 10:
            insights.append(f"Spending increased by **{sc['percent_change']:.0f}%** compared to the previous week.")
        elif sc["percent_change"] < -10:
            insights.append(f"Good job — spending decreased by **{abs(sc['percent_change']):.0f}%** from last week.")
        else:
            insights.append("Spending is stable compared to last week.")

    rec = detect_recurring(username)
    if rec:
        names = ", ".join([r["note"] for r in rec[:3]])
        insights.append(f"Detected recurring charges: {names}. Consider adding them to 'Subscriptions'.")

    if not df.empty:
        largest = df.sort_values(by="Amount", ascending=False).head(1)
        if not largest.empty and largest.iloc[0]["Amount"] > (df["Amount"].mean() * 3):
            insights.append(
                f"A large transaction detected: ₹{largest.iloc[0]['Amount']:.2f} on {largest.iloc[0]['Date']}."
            )

    return insights


# =====================================================================
# AI assistant — natural-language query handler
# =====================================================================

def ai_answer(username: str, user_question: str) -> str:
    """Return a plain-text answer to a spending question."""
    q = user_question.strip().lower()
    df = load_expenses(username)

    if df.empty:
        return "No expenses recorded yet. Add expenses or upload CSV so I can analyze your spending."

    # --- Overspending ---
    if "overspend" in q or "where am i overspending" in q or "overspending" in q:
        top30 = category_summary(username, 30)
        if top30.empty:
            return "I couldn't find spending records for the last 30 days."
        top = top30.index[0]
        pct = (top30.iloc[0] / top30.sum()) * 100 if top30.sum() > 0 else 0
        return (
            f"You're spending most on **{top}** — {pct:.0f}% of month spending. "
            f"Try limiting frequency or set a sub-budget for {top}."
        )

    # --- Top categories ---
    if "top categories" in q or "top category" in q:
        topN = category_summary(username, 90).head(5)
        if topN.empty:
            return "No category data found."
        lines = [f"{i+1}. {cat}: ₹{amt:.2f}" for i, (cat, amt) in enumerate(topN.items())]
        return "Top categories (last 90 days):\n" + "\n".join(lines)

    # --- This month ---
    if "this month" in q and "spent" in q:
        start = datetime.today().replace(day=1)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        month_sum = df[df["Date"] >= start]["Amount"].sum()
        return f"You've spent ₹{month_sum:.2f} this month so far."

    # --- Saving tips ---
    if "how to save" in q or "tips" in q:
        top30 = category_summary(username, 30)
        tips = []
        if not top30.empty:
            top = top30.index[0]
            tips.append(f"Cut down {top} by 10% and save ₹{(top30.iloc[0] * 0.1):.0f} monthly.")
        tips.append("Unsubscribe unused services; cook at home; set weekly budgets.")
        return "Suggested actions:\n- " + "\n- ".join(tips)

    # --- Recurring / subscriptions ---
    if "recurring" in q or "subscription" in q:
        rec = detect_recurring(username)
        if not rec:
            return "No obvious recurring charges detected."
        lines = [f"{r['note']} — {r['count']} times, avg ₹{r['avg']:.2f}" for r in rec]
        return "Recurring payments found:\n" + "\n".join(lines)

    # --- General summary ---
    if q in ("summary", "give me summary", "overview"):
        insights = generate_insights(username)
        return "\n".join(insights)

    return "Sorry — try: 'Where am I overspending?', 'How much this month?', 'Top categories', or 'Any subscriptions?'"


# =====================================================================
# Chart saving
# =====================================================================

def save_chart(fig, chart_name: str, username: str = "") -> str:
    """Save a matplotlib figure to the reports/ directory and return the path."""
    prefix = f"{username}_" if username else ""
    filename = f"{prefix}{chart_name}.png"
    path = os.path.join(REPORTS_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    return path
