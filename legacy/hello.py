import streamlit as st
import csv
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

EXPENSE_FILE = 'expenses.csv'
LIMIT_FILE = 'limit.txt'

def set_weekly_limit(new_limit):
    with open(LIMIT_FILE, 'w') as f:
        f.write(str(new_limit))

def get_weekly_limit():
    try:
        with open(LIMIT_FILE, 'r') as f:
            return float(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 1000  # default

def add_expense(amount, category, note):
    date = datetime.today().strftime('%Y-%m-%d')
    with open(EXPENSE_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['Date', 'Amount', 'Category', 'Note'])
        writer.writerow([date, amount, category, note])

def load_expenses():
    try:
        with open(EXPENSE_FILE, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            return list(reader)
    except FileNotFoundError:
        return []

def weekly_summary():
    today = datetime.today()
    week_ago = today - timedelta(days=7)
    summary = {}
    data = load_expenses()
    for row in data:
        date_str, amount, category, *_ = row
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if week_ago <= date <= today:
            summary[category] = summary.get(category, 0) + float(amount)
    return summary

def calendar_summary():
    today = datetime.today()
    week_ago = today - timedelta(days=6)
    days = { (week_ago + timedelta(days=i)).strftime('%a (%d %b)'): 0 for i in range(7) }
    data = load_expenses()
    for row in data:
        date_str, amount, *_ = row
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if week_ago <= date <= today:
            key = date.strftime('%a (%d %b)')
            days[key] += float(amount)
    return days

def total_weekly_spending():
    today = datetime.today()
    week_ago = today - timedelta(days=7)
    total = 0
    data = load_expenses()
    for row in data:
        date_str, amount, *_ = row
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if week_ago <= date <= today:
            total += float(amount)
    return total

def main():
    st.set_page_config(page_title="Expense Tracker", layout="centered")
    st.title("📊 Personal Expense Tracker")

    menu = ["Add Expense", "View Weekly Summary", "Calendar View", "Search Expenses", "Set Weekly Limit"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add Expense":
        st.subheader("➕ Add New Expense")
        amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01)
        category = st.text_input("Category")
        note = st.text_input("Note (optional)")
        if st.button("Add"):
            add_expense(amount, category, note)
            st.success("Expense added successfully!")

    elif choice == "View Weekly Summary":
        st.subheader("📊 Weekly Expense Summary")
        summary = weekly_summary()
        if summary:
            fig, ax = plt.subplots()
            ax.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
            ax.set_title('Weekly Expense Distribution')
            st.pyplot(fig)

            total = sum(summary.values())
            limit = get_weekly_limit()
            if total > limit:
                st.warning(f"⚠️ You've spent ₹{total:.2f}, which exceeds your ₹{limit:.2f} weekly limit!")
            else:
                st.success(f"✅ You're within your weekly limit. Total spent: ₹{total:.2f}")
        else:
            st.info("No expenses recorded in the last 7 days.")

    elif choice == "Calendar View":
        st.subheader("🗓️ Weekly Calendar View")
        calendar = calendar_summary()
        for day, amount in calendar.items():
            st.write(f"{day}: ₹{amount:.2f}")

        total = total_weekly_spending()
        limit = get_weekly_limit()
        if total > limit:
            st.warning(f"⚠️ Weekly spending ₹{total:.2f} exceeds your ₹{limit:.2f} limit!")
        else:
            st.success(f"✅ Weekly spending ₹{total:.2f} is within your ₹{limit:.2f} limit.")

    elif choice == "Search Expenses":
        st.subheader("🔍 Search Expenses")
        query = st.text_input("Enter date (YYYY-MM-DD) or keyword")
        if query:
            found = False
            data = load_expenses()
            for row in data:
                if any(query.lower() in str(col).lower() for col in row):
                    st.write(row)
                    found = True
            if not found:
                st.warning("No matching records found.")

    elif choice == "Set Weekly Limit":
        st.subheader("💰 Set Weekly Spending Limit")
        limit = st.number_input("Enter new weekly limit (₹)", min_value=0.0, step=10.0)
        if st.button("Set Limit"):
            set_weekly_limit(limit)
            st.success(f"Weekly limit set to ₹{limit:.2f}")

if __name__ == '__main__':
    main()