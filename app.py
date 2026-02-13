# app.py
# SmartSpends — Streamlit entry point.
# All business logic lives in src/; this file handles UI rendering and routing.

from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.utils import DEFAULT_THEME, parse_date_flexibly, load_css, toggle_theme
from src.storage import load_expenses, get_weekly_limit, set_weekly_limit, save_expenses_df
from src.tracker import (
    register_user,
    verify_user,
    add_expense,
    weekly_expense_total,
    get_razorpay_client,
    create_order,
)
from src.analytics import (
    get_time_series,
    category_summary,
    daily_heatmap,
    detect_recurring,
    generate_insights,
    ai_answer,
    save_chart,
)


# =====================================================================
# Page config (MUST be the first Streamlit call)
# =====================================================================
st.set_page_config(page_title="SmartSpends", layout="wide", initial_sidebar_state="collapsed")

if "theme" not in st.session_state:
    st.session_state["theme"] = DEFAULT_THEME

load_css(st.session_state["theme"])


# =====================================================================
# Auth UI — login / register (shown when not logged in)
# =====================================================================
def auth_ui():
    st.markdown("<div class='center-card'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div><div class='brand'>💳 SmartSpends</div>"
        "<div class='subtitle'>Personal finance, but smarter. "
        "Securely store and analyze your spending.</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    tabs = st.tabs(["Login", "Register"])

    # ---- Login tab ----
    with tabs[0]:
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        st.subheader("Welcome back")
        st.markdown(
            "<div class='small-muted'>Login to access your personalized dashboard.</div>",
            unsafe_allow_html=True,
        )
        with st.form("login_form_tab"):
            uname = st.text_input("Username", key="tab_login_user")
            pw = st.text_input("Password", type="password", key="tab_login_pass")
            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("Login")
            with col2:
                demo = st.form_submit_button("Use Demo (guest)")
        if demo:
            uname, pw = "guest", "1234"
            if verify_user(uname, pw):
                st.session_state["user"] = uname
                st.success("Logged in as guest.")
                st.rerun()
        if submitted:
            if verify_user(uname, pw):
                st.session_state["user"] = uname
                st.success(f"Welcome back, {uname}!")
                st.rerun()
            else:
                st.error("Invalid username or password. Try demo guest / 1234.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Register tab ----
    with tabs[1]:
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        st.subheader("Create account")
        st.markdown(
            "<div class='small-muted'>Sign up to keep your expenses private and separated.</div>",
            unsafe_allow_html=True,
        )
        with st.form("register_form_tab"):
            new_user = st.text_input("Choose a username", key="tab_reg_user")
            new_pass = st.text_input("Password", type="password", key="tab_reg_pass")
            new_pass2 = st.text_input("Confirm password", type="password", key="tab_reg_pass2")
            reg_sub = st.form_submit_button("Register")
        if reg_sub:
            if new_pass != new_pass2:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_user(new_user, new_pass)
                if ok:
                    st.success("Registered — logging you in.")
                    st.session_state["user"] = new_user
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<div style='margin-top:12px;' class='small-muted'>"
        "Tip: demo user — username: <b>guest</b> password: <b>1234</b></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    colA, colB, colC = st.columns([3, 1, 1])
    with colB:
        if st.button("🌗 Toggle Theme (Session)"):
            toggle_theme()
            st.rerun()
    with colC:
        st.button("About")
    st.markdown(
        "<div class='footer'>💳 SmartSpends — Built by Pratham (2025)</div>",
        unsafe_allow_html=True,
    )


# Gate: require login
if "user" not in st.session_state:
    auth_ui()
    st.stop()

USERNAME = st.session_state["user"]


# =====================================================================
# Sidebar navigation
# =====================================================================
with st.sidebar:
    st.markdown("<h3 style='color:#00E5FF;'>💳 SmartSpends</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='small-muted'>Logged in as: <b>{USERNAME}</b></div>", unsafe_allow_html=True)
    st.markdown("---")
    nav = st.radio(
        "",
        (
            "Home",
            "Add Expense",
            "View Summary",
            "Analytics",
            "AI Assistant",
            "Upload Bank CSV",
            "Online Payment (Razorpay)",
        ),
    )
    st.markdown("---")
    if st.button("🚪 Logout"):
        del st.session_state["user"]
        st.rerun()
    if st.button("🌗 Toggle Theme"):
        toggle_theme()
        st.rerun()
    st.markdown(
        "<div class='small-muted'>💳 SmartSpends — Built by Pratham (2025)</div>",
        unsafe_allow_html=True,
    )


# =====================================================================
# Page renderers
# =====================================================================

def page_home():
    col1, col2 = st.columns([4, 1])
    with col1:
        hour = datetime.now().hour
        greet = "Good Morning ☀️" if hour < 12 else ("Good Afternoon 🌞" if hour < 18 else "Good Evening 🌙")
        st.markdown(f"<h2 class='brand' style='color:#00E5FF'>{greet}, {USERNAME} 👋</h2>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-muted'>{datetime.now().strftime('%A, %d %B %Y')}</div>", unsafe_allow_html=True)
    with col2:
        if st.button("➕ Quick Add"):
            st.session_state["nav_to_add"] = True
            st.rerun()

    st.markdown("---")
    df_all = load_expenses(USERNAME)
    weekly = weekly_expense_total(USERNAME)
    limit = get_weekly_limit(USERNAME)
    remaining = max(limit - weekly, 0)
    tx_count = len(df_all) if not df_all.empty else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"<div class='form-card'><h4>💰 Weekly Spent</h4>"
            f"<h2 style='color:#00E5FF;'>₹{weekly:.2f}</h2>"
            f"<div class='small-muted'>This week</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='form-card'><h4>🎯 Limit Remaining</h4>"
            f"<h2 style='color:#7C4DFF;'>₹{remaining:.2f}</h2>"
            f"<div class='small-muted'>Out of ₹{limit:.2f}</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='form-card'><h4>📅 Transactions</h4>"
            f"<h2 style='color:#00C853;'>{tx_count}</h2>"
            f"<div class='small-muted'>Total recorded</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("<div class='form-card'><h4>Quick Insights</h4>", unsafe_allow_html=True)
    for s in generate_insights(USERNAME):
        st.markdown(f"- {s}")
    st.markdown("</div>", unsafe_allow_html=True)


def page_add_expense():
    st.header("➕ Add New Expense")
    amt = st.number_input("Amount (₹)", min_value=0.0, step=0.5, format="%.2f")
    cat = st.text_input("Category", max_chars=40)
    note = st.text_input("Note", max_chars=120)
    date_in = st.date_input("Date", value=datetime.today())
    if st.button("Add"):
        if amt > 0 and cat.strip() != "":
            add_expense(USERNAME, amt, cat, note, date=date_in)
            st.success("Expense added.")
        else:
            st.error("Provide amount and category.")
    st.session_state["nav_to_add"] = False


def page_view_summary():
    st.header("📊 Expense Summary")
    df = load_expenses(USERNAME)
    if df.empty:
        st.info("No expenses yet.")
        return
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    show_all = st.checkbox("Show all", value=False)
    if show_all:
        filtered = df.copy()
    else:
        week_ago = datetime.today() - timedelta(days=7)
        filtered = df[df["Date"] >= week_ago]
    st.dataframe(filtered, use_container_width=True)
    st.metric("💸 Total Spent", f"₹{filtered['Amount'].sum():.2f}")


def page_analytics():
    st.header("📈 Analytics Dashboard")
    df = load_expenses(USERNAME)
    if df.empty:
        st.info("No data yet. Add or import transactions to see analytics.")
        return

    is_dark = st.session_state["theme"] == "dark"
    months = st.selectbox("Show last N months", [1, 3, 6, 12], index=1)

    # ---- Spending Trend ----
    ts = get_time_series(USERNAME, freq="D", months=months)
    st.markdown("<div class='form-card'><h4>Spending Trend</h4>", unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(8, 3))
    if is_dark:
        fig.patch.set_facecolor("#0B0B0B")
        ax.set_facecolor("#0B0B0B")
        ax.plot(ts.index, ts.values, color="#00E5FF")
        ax.tick_params(colors="white")
        ax.spines["bottom"].set_color("gray")
        ax.spines["left"].set_color("gray")
    else:
        fig.patch.set_facecolor("#fff")
        ax.set_facecolor("#fff")
        ax.plot(ts.index, ts.values, color="#0077b6")
    ax.set_ylabel("₹")
    st.pyplot(fig)
    save_chart(fig, "spending_trend", USERNAME)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Category Comparison ----
    st.markdown("<div class='form-card'><h4>Category Comparison (last 30 days)</h4>", unsafe_allow_html=True)
    cat30 = category_summary(USERNAME, 30)
    if cat30.empty:
        st.info("Not enough category data.")
    else:
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        cats = cat30.index[:8]
        vals = cat30.values[:8]
        colors = ["#00E5FF", "#7C4DFF", "#00C853", "#FF1744", "#FFA726", "#FFB74D", "#8E24AA", "#42A5F5"]
        ax2.barh(cats[::-1], vals[::-1], color=colors[: len(cats)])
        if is_dark:
            ax2.set_facecolor("#0B0B0B")
            fig2.patch.set_facecolor("#0B0B0B")
            ax2.tick_params(colors="white")
        st.pyplot(fig2)
        save_chart(fig2, "category_comparison", USERNAME)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Weekday Spending ----
    st.markdown("<div class='form-card'><h4>Weekday Spending (last 30 days)</h4>", unsafe_allow_html=True)
    heat = daily_heatmap(USERNAME, 30)
    if heat is None or heat.sum() == 0:
        st.info("No weekday pattern yet.")
    else:
        fig3, ax3 = plt.subplots(figsize=(6, 2))
        ax3.bar(heat.index, heat.values, color="#00E5FF" if is_dark else "#0077b6")
        if is_dark:
            ax3.set_facecolor("#0B0B0B")
            fig3.patch.set_facecolor("#0B0B0B")
            ax3.tick_params(colors="white")
        st.pyplot(fig3)
        save_chart(fig3, "weekday_spending", USERNAME)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Recurring Payments ----
    st.markdown("<div class='form-card'><h4>Detected Recurring Payments</h4>", unsafe_allow_html=True)
    recs = detect_recurring(USERNAME)
    if not recs:
        st.write("No recurring payments detected.")
    else:
        for r in recs:
            st.write(f"- {r['note']} — {r['count']} times, avg ₹{r['avg']:.2f}")
    st.markdown("</div>", unsafe_allow_html=True)


def page_ai_assistant():
    st.header("💬 AI Assistant — Ask about your spending")
    st.markdown("Ask in plain English, e.g. *Where am I overspending?*, *How much this month?*, *Any subscriptions?*")
    q = st.text_input("Ask SmartSpends:", key="ai_query")
    if st.button("Ask") and q.strip() != "":
        with st.spinner("Analyzing..."):
            ans = ai_answer(USERNAME, q)
        st.markdown("**Answer:**")
        st.write(ans)
    st.markdown("---")
    st.markdown("<div class='form-card'><h4>Auto Insights (one-click)</h4>", unsafe_allow_html=True)
    if st.button("Generate Insights"):
        with st.spinner("Generating insights..."):
            ins = generate_insights(USERNAME)
        for i in ins:
            st.markdown(f"- {i}")
    st.markdown("</div>", unsafe_allow_html=True)


def page_upload_csv():
    st.header("🏦 Upload Bank Statement (CSV)")
    uploaded_file = st.file_uploader("Choose CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            bdf = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(bdf.head())

            possible_debit_cols = [c for c in bdf.columns if "debit" in c.lower() or "withdraw" in c.lower() or "amount" in c.lower()]
            possible_date_cols = [c for c in bdf.columns if "date" in c.lower()]
            possible_desc_cols = [c for c in bdf.columns if "desc" in c.lower() or "narration" in c.lower() or "details" in c.lower()]

            debit_col = possible_debit_cols[0] if possible_debit_cols else st.selectbox("Select debit column", bdf.columns)
            date_col = possible_date_cols[0] if possible_date_cols else st.selectbox("Select date column", bdf.columns)
            desc_col = possible_desc_cols[0] if possible_desc_cols else st.selectbox("Select description column", bdf.columns)

            debit_df = bdf[bdf[debit_col].notna()][[date_col, debit_col, desc_col]].copy()
            debit_df.columns = ["Date", "Amount", "Note"]
            debit_df["Category"] = "Bank Debit"
            debit_df["Date"] = debit_df["Date"].apply(parse_date_flexibly)
            debit_df = debit_df.dropna(subset=["Date"])
            debit_df["Amount"] = debit_df["Amount"].astype(float)

            existing = load_expenses(USERNAME)
            combined = pd.concat([existing, debit_df[["Date", "Amount", "Category", "Note"]]], ignore_index=True)
            save_expenses_df(USERNAME, combined)
            st.success(f"Imported {len(debit_df)} debits.")
        except Exception as e:
            st.error(f"Error: {e}")


def page_razorpay():
    st.header("💳 Razorpay (Test Mode)")
    rclient = get_razorpay_client()
    amount = st.number_input("Amount (₹)", min_value=1.0, step=1.0, format="%.2f")
    category = st.text_input("Category", "Online Payment")
    note = st.text_input("Note", "Razorpay Test")
    if st.button("Create Test Order & Log"):
        try:
            order = create_order(rclient, amount)
            st.success("Order created (test).")
            st.json(order)
            add_expense(USERNAME, amount, category, note)
            st.success("Logged to expenses.")
        except Exception as e:
            st.error(f"Error: {e}")


# =====================================================================
# Routing
# =====================================================================
PAGES = {
    "Home": page_home,
    "Add Expense": page_add_expense,
    "View Summary": page_view_summary,
    "Analytics": page_analytics,
    "AI Assistant": page_ai_assistant,
    "Upload Bank CSV": page_upload_csv,
    "Online Payment (Razorpay)": page_razorpay,
}

# Support "Quick Add" button redirect from Home
if st.session_state.get("nav_to_add"):
    page_add_expense()
else:
    PAGES[nav]()
