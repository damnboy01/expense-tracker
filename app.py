# app.py
import os, json, hashlib, secrets, csv
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Optional razorpay
try:
    import razorpay
except Exception:
    razorpay = None

# ---------------- CONFIG / AUTH HELPERS ----------------
USERS_FILE = "users.json"
def hash_with_salt(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()

def _ensure_users_file():
    if not os.path.exists(USERS_FILE):
        salt = secrets.token_hex(8)
        pw_hash = hash_with_salt("1234", salt)
        users = {"guest": {"salt": salt, "pw_hash": pw_hash}}
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

def load_users():
    _ensure_users_file()
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def register_user(username, password):
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

def verify_user(username, password):
    users = load_users()
    if username not in users:
        return False
    salt = users[username]["salt"]
    return users[username]["pw_hash"] == hash_with_salt(password, salt)

# ---------------- THEME / CSS ----------------
st.set_page_config(page_title="SmartSpends", layout="wide", initial_sidebar_state="collapsed")
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

def toggle_theme():
    st.session_state["theme"] = "light" if st.session_state["theme"]=="dark" else "dark"

def load_css(theme):
    if theme=="dark":
        st.markdown("""
        <style>
        :root{
          --bg:#0B0B0B; --card: rgba(24,24,24,0.92); --text:#E6EEF3;
          --accent:#00E5FF; --accent2:#7C4DFF; --muted:#9AA3A9;
        }
        html, body, [class*="css"]  { background:var(--bg) !important; color:var(--text) !important; }
        .center-card {
          max-width:920px; margin:40px auto; padding:28px; border-radius:14px;
          background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));
          box-shadow: 0 12px 40px rgba(0,0,0,0.7); border:1px solid rgba(255,255,255,0.02);
        }
        .brand { font-size:30px; font-weight:700; color:var(--accent); margin-bottom:6px; }
        .subtitle { color:var(--muted); margin-bottom:18px; }
        .auth-left { padding-right:18px; border-right:1px solid rgba(255,255,255,0.02); }
        .auth-right { padding-left:18px; }
        .form-card { background: rgba(10,10,10,0.6); padding:18px; border-radius:10px; border:1px solid rgba(255,255,255,0.02); }
        .btn-primary { background: linear-gradient(90deg,var(--accent),var(--accent2)); color:#07100f; padding:10px 16px; border-radius:10px; font-weight:600; border:none; }
        .small-muted { color:var(--muted); font-size:13px; }
        input, textarea { background: rgba(255,255,255,0.02) !important; color:var(--text) !important; }
        .stTextInput>div>div>input { height:44px; padding:12px; border-radius:8px; }
        .stNumberInput>div>input { height:44px; padding:12px; border-radius:8px; }
        .footer { text-align:center; color:var(--muted); padding:18px 0; }
        .tabbed { display:flex; gap:8px; margin-bottom:12px; }
        .tabbed button { padding:8px 12px; border-radius:8px; border:1px solid rgba(255,255,255,0.02); background:transparent; color:var(--text); }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        :root{
          --bg:#FAFBFD; --card:#FFFFFF; --text:#0E1116;
          --accent:#0077b6; --accent2:#6a00f4; --muted:#6b6b6b;
        }
        html, body, [class*="css"]  { background:var(--bg) !important; color:var(--text) !important; }
        .center-card { max-width:920px; margin:40px auto; padding:28px; border-radius:14px; background: var(--card); box-shadow:0 12px 30px rgba(16,24,40,0.04); border:1px solid rgba(0,0,0,0.04); }
        .brand { font-size:30px; font-weight:700; color:var(--accent); margin-bottom:6px; }
        .subtitle { color:var(--muted); margin-bottom:18px; }
        .auth-left { padding-right:18px; border-right:1px solid rgba(0,0,0,0.04); }
        .auth-right { padding-left:18px; }
        .form-card { background: #f7f9fc; padding:18px; border-radius:10px; border:1px solid rgba(0,0,0,0.04); }
        .btn-primary { background: linear-gradient(90deg,var(--accent),var(--accent2)); color:white; padding:10px 16px; border-radius:10px; font-weight:600; border:none; }
        .small-muted { color:var(--muted); font-size:13px; }
        input, textarea { background: rgba(0,0,0,0.02) !important; color:var(--text) !important; }
        .stTextInput>div>div>input { height:44px; padding:12px; border-radius:8px; }
        .stNumberInput>div>input { height:44px; padding:12px; border-radius:8px; }
        .footer { text-align:center; color:var(--muted); padding:18px 0; }
        </style>
        """, unsafe_allow_html=True)

load_css(st.session_state["theme"])

# ---------------- AUTH UI (TABBED POLISHED) ----------------
def auth_ui_tabbed():
    st.markdown("<div class='center-card'>", unsafe_allow_html=True)
    # Header
    st.markdown("<div style='display:flex;justify-content:space-between;align-items:center;'>", unsafe_allow_html=True)
    st.markdown("<div><div class='brand'>💳 SmartSpends</div><div class='subtitle'>Personal finance, but smarter. Securely store and analyze your spending.</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Use tabs inside center card
    tabs = st.tabs(["Login", "Register"])
    # LOGIN TAB
    with tabs[0]:
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        st.subheader("Welcome back")
        st.markdown("<div class='small-muted'>Login to access your personalized dashboard.</div>", unsafe_allow_html=True)
        with st.form("login_form_tab"):
            uname = st.text_input("Username", key="tab_login_user")
            pw = st.text_input("Password", type="password", key="tab_login_pass")
            col1, col2 = st.columns([1,1])
            with col1:
                submitted = st.form_submit_button("Login")
            with col2:
                demo = st.form_submit_button("Use Demo (guest)")
        # handle demo quickly
        if demo:
            uname = "guest"; pw = "1234"
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

    # REGISTER TAB
    with tabs[1]:
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        st.subheader("Create account")
        st.markdown("<div class='small-muted'>Sign up to keep your expenses private and separated.</div>", unsafe_allow_html=True)
        with st.form("register_form_tab"):
            new_user = st.text_input("Choose a username", key="tab_reg_user")
            new_pass = st.text_input("Password", type="password", key="tab_reg_pass")
            new_pass2 = st.text_input("Confirm password", type="password", key="tab_reg_pass2")
            reg_sub = st.form_submit_button("Register")
        if reg_sub:
            if new_pass != new_pass2:
                st.error("Passwords do not match.")
            else:
                ok,msg = register_user(new_user, new_pass)
                if ok:
                    st.success("Registered — logging you in.")
                    st.session_state["user"] = new_user
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    # footer inside card
    st.markdown("<div style='margin-top:12px;' class='small-muted'>Tip: demo user — username: <b>guest</b> password: <b>1234</b></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    # theme toggle below card
    colA, colB, colC = st.columns([3,1,1])
    with colB:
        if st.button("🌗 Toggle Theme (Session)"):
            toggle_theme()
            st.rerun()
    with colC:
        st.button("About")  # placeholder
    st.markdown("<div class='footer'>💳 SmartSpends — Built by Pratham (2025)</div>", unsafe_allow_html=True)

# If user not logged in → show improved auth UI and stop
if "user" not in st.session_state:
    auth_ui_tabbed()
    st.stop()

# ---------------- per-user files & razorpay ----------------
USERNAME = st.session_state["user"]
EXPENSE_FILE = f"expenses_{USERNAME}.csv"
LIMIT_FILE = f"limit_{USERNAME}.txt"

# Razorpay client (optional)
RAZORPAY_KEY_ID = "rzp_test_RSrYrIik3LfPzl"
RAZORPAY_KEY_SECRET = "tOrAIpnwpns10tG2YHy2Q5TK"
if razorpay:
    try:
        rclient = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        rclient = None
else:
    rclient = None

# ---------------- expense helpers ----------------
def get_weekly_limit():
    if os.path.exists(LIMIT_FILE):
        try:
            return float(open(LIMIT_FILE).read())
        except:
            return 1000.0
    return 1000.0

def set_weekly_limit(limit):
    with open(LIMIT_FILE, "w") as f:
        f.write(str(limit))

def add_expense(amount, category, note, date=None):
    if isinstance(date, datetime):
        date_str = date.strftime("%Y-%m-%d")
    elif isinstance(date, str) and date:
        date_str = date
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")
    exists = os.path.exists(EXPENSE_FILE)
    with open(EXPENSE_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if (not exists) or (os.path.getsize(EXPENSE_FILE)==0):
            w.writerow(["Date","Amount","Category","Note"])
        w.writerow([date_str, float(amount), category, note])

def load_expenses():
    if os.path.exists(EXPENSE_FILE):
        try:
            df = pd.read_csv(EXPENSE_FILE)
            return df
        except:
            return pd.DataFrame(columns=["Date","Amount","Category","Note"])
    return pd.DataFrame(columns=["Date","Amount","Category","Note"])

def parse_date_flexibly(x):
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d-%m-%Y","%m/%d/%Y","%d.%m.%Y"):
        try:
            return datetime.strptime(str(x).strip(), fmt).strftime("%Y-%m-%d")
        except:
            continue
    try:
        return pd.to_datetime(x, dayfirst=True, errors='coerce').strftime('%Y-%m-%d')
    except:
        return None

def weekly_expense_total():
    df = load_expenses()
    if df.empty:
        return 0.0
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    week_ago = datetime.today() - timedelta(days=7)
    df = df[df['Date'] >= week_ago]
    return df['Amount'].sum()

# ---------------- ANALYTICS & AI ----------------
def get_time_series(freq='D', months=3):
    df = load_expenses()
    if df.empty:
        return pd.Series(dtype=float)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    start = datetime.today() - pd.DateOffset(months=months)
    df = df[df['Date'] >= start]
    ts = df.set_index('Date').resample(freq)['Amount'].sum().fillna(0)
    return ts

def category_summary(period_days=30):
    df = load_expenses()
    if df.empty:
        return pd.Series(dtype=float)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    since = datetime.today() - timedelta(days=period_days)
    df = df[df['Date'] >= since]
    agg = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    return agg

def daily_heatmap(days=30):
    df = load_expenses()
    if df.empty:
        return None
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    since = datetime.today() - timedelta(days=days)
    df = df[df['Date'] >= since]
    pivot = df.groupby(df['Date'].dt.day_name())['Amount'].sum().reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).fillna(0)
    return pivot

def detect_recurring(min_occurrences=3, window_days=90):
    df = load_expenses()
    if df.empty:
        return []
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    since = datetime.today() - timedelta(days=window_days)
    df = df[df['Date'] >= since]
    candidates = df.groupby('Note')['Amount'].agg(['count','mean']).sort_values('count', ascending=False)
    recurring = []
    for idx, row in candidates.iterrows():
        if row['count'] >= min_occurrences:
            recurring.append({"note": idx, "count": int(row['count']), "avg": float(row['mean'])})
    return recurring

def spending_change(period_days=7):
    df = load_expenses()
    if df.empty:
        return {}
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    end = datetime.today()
    start = end - timedelta(days=period_days)
    prev_start = start - timedelta(days=period_days)
    recent_sum = df[(df['Date'] >= start) & (df['Date'] < end)]['Amount'].sum()
    prev_sum = df[(df['Date'] >= prev_start) & (df['Date'] < prev_start+timedelta(days=period_days))]['Amount'].sum()
    change = None
    if prev_sum == 0:
        change = None
    else:
        change = ((recent_sum - prev_sum) / prev_sum) * 100
    return {"recent": float(recent_sum), "previous": float(prev_sum), "percent_change": change}

def generate_insights():
    insights = []
    df = load_expenses()
    if df.empty:
        insights.append("No expenses recorded yet. Add some expenses or upload a bank CSV to get insights.")
        return insights
    top_cats = category_summary(30)
    if not top_cats.empty:
        top = top_cats.index[0]
        pct = (top_cats.iloc[0] / top_cats.sum())*100 if top_cats.sum()>0 else 0
        insights.append(f"In the last 30 days, your top category is **{top}** accounting for **{pct:.0f}%** of your spending.")
    sc = spending_change(7)
    if sc:
        if sc['percent_change'] is None:
            insights.append(f"Your spending last 7 days: ₹{sc['recent']:.2f}. No previous period to compare.")
        else:
            if sc['percent_change'] > 10:
                insights.append(f"Spending increased by **{sc['percent_change']:.0f}%** compared to the previous week.")
            elif sc['percent_change'] < -10:
                insights.append(f"Good job — spending decreased by **{abs(sc['percent_change']):.0f}%** from last week.")
            else:
                insights.append("Spending is stable compared to last week.")
    rec = detect_recurring()
    if rec:
        sample = rec[:3]
        names = ", ".join([r['note'] for r in sample])
        insights.append(f"Detected recurring charges: {names}. Consider adding them to 'Subscriptions'.")
    if not df.empty:
        largest = df.sort_values(by='Amount', ascending=False).head(1)
        if not largest.empty and largest.iloc[0]['Amount'] > (df['Amount'].mean() * 3):
            insights.append(f"A large transaction detected: ₹{largest.iloc[0]['Amount']:.2f} on {largest.iloc[0]['Date']}.")
    return insights

def ai_answer(user_question):
    q = user_question.strip().lower()
    df = load_expenses()
    if df.empty:
        return "No expenses recorded yet. Add expenses or upload CSV so I can analyze your spending."
    if "overspend" in q or "where am i overspending" in q or "overspending" in q:
        top30 = category_summary(30)
        if top30.empty:
            return "I couldn't find spending records for the last 30 days."
        top = top30.index[0]
        pct = (top30.iloc[0] / top30.sum())*100 if top30.sum()>0 else 0
        suggestion = f"You're spending most on **{top}** — {pct:.0f}% of month spending. Try limiting frequency or set a sub-budget for {top}."
        return suggestion
    if "top categories" in q or "top category" in q:
        topN = category_summary(90).head(5)
        if topN.empty:
            return "No category data found."
        lines = [f"{i+1}. {cat}: ₹{amt:.2f}" for i,(cat,amt) in enumerate(topN.items())]
        return "Top categories (last 90 days):\n" + "\n".join(lines)
    if "this month" in q and "spent" in q:
        start = datetime.today().replace(day=1)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        month_sum = df[df['Date']>=start]['Amount'].sum()
        return f"You've spent ₹{month_sum:.2f} this month so far."
    if "how to save" in q or "tips" in q:
        top30 = category_summary(30)
        tips = []
        if not top30.empty:
            top = top30.index[0]
            tips.append(f"Cut down {top} by 10% and save ₹{(top30.iloc[0]*0.1):.0f} monthly.")
        tips.append("Unsubscribe unused services; cook at home; set weekly budgets.")
        return "Suggested actions:\n- " + "\n- ".join(tips)
    if "recurring" in q or "subscription" in q:
        rec = detect_recurring()
        if not rec:
            return "No obvious recurring charges detected."
        lines = [f"{r['note']} — {r['count']} times, avg ₹{r['avg']:.2f}" for r in rec]
        return "Recurring payments found:\n" + "\n".join(lines)
    if q in ("summary","give me summary","overview"):
        insights = generate_insights()
        return "\n".join(insights)
    return "Sorry — try: 'Where am I overspending?', 'How much this month?', 'Top categories', or 'Any subscriptions?'"

# ---------------- SIDEBAR / NAV ----------------
with st.sidebar:
    st.markdown(f"<h3 style='color:#00E5FF;'>💳 SmartSpends</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='small-muted'>Logged in as: <b>{USERNAME}</b></div>", unsafe_allow_html=True)
    st.markdown("---")
    nav = st.radio("", ("Home","Add Expense","View Summary","Analytics","AI Assistant","Upload Bank CSV","Online Payment (Razorpay)"))
    st.markdown("---")
    if st.button("🚪 Logout"):
        del st.session_state["user"]
        st.rerun()
    if st.button("🌗 Toggle Theme"):
        toggle_theme()
        st.rerun()
    st.markdown("<div class='small-muted'>💳 SmartSpends — Built by Pratham (2025)</div>", unsafe_allow_html=True)

# ---------------- PAGES ----------------
# Home
if nav=="Home":
    col1,col2 = st.columns([4,1])
    with col1:
        hour = datetime.now().hour
        greet = "Good Morning ☀️" if hour<12 else ("Good Afternoon 🌞" if hour<18 else "Good Evening 🌙")
        st.markdown(f"<h2 class='brand' style='color:#00E5FF'>{greet}, {USERNAME} 👋</h2>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-muted'>{datetime.now().strftime('%A, %d %B %Y')}</div>", unsafe_allow_html=True)
    with col2:
        if st.button("➕ Quick Add"):
            st.session_state['nav_to_add'] = True
            st.rerun()
    st.markdown("---")
    df_all = load_expenses()
    weekly = weekly_expense_total()
    limit = get_weekly_limit()
    remaining = max(limit-weekly,0)
    tx_count = len(df_all) if not df_all.empty else 0
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='form-card'><h4>💰 Weekly Spent</h4><h2 style='color:#00E5FF;'>₹{weekly:.2f}</h2><div class='small-muted'>This week</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='form-card'><h4>🎯 Limit Remaining</h4><h2 style='color:#7C4DFF;'>₹{remaining:.2f}</h2><div class='small-muted'>Out of ₹{limit:.2f}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='form-card'><h4>📅 Transactions</h4><h2 style='color:#00C853;'>{tx_count}</h2><div class='small-muted'>Total recorded</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div class='form-card'><h4>Quick Insights</h4>", unsafe_allow_html=True)
    ins = generate_insights()
    for s in ins:
        st.markdown(f"- {s}")
    st.markdown("</div>", unsafe_allow_html=True)

# Add Expense
elif nav=="Add Expense" or st.session_state.get('nav_to_add'):
    st.header("➕ Add New Expense")
    amt = st.number_input("Amount (₹)", min_value=0.0, step=0.5, format="%.2f")
    cat = st.text_input("Category", max_chars=40)
    note = st.text_input("Note", max_chars=120)
    date_in = st.date_input("Date", value=datetime.today())
    if st.button("Add"):
        if amt>0 and cat.strip()!="":
            add_expense(amt, cat, note, date=date_in)
            st.success("Expense added.")
        else:
            st.error("Provide amount and category.")
    st.session_state['nav_to_add'] = False

# View Summary
elif nav=="View Summary":
    st.header("📊 Expense Summary")
    df = load_expenses()
    if df.empty:
        st.info("No expenses yet.")
    else:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        show_all = st.checkbox("Show all", value=False)
        if show_all:
            filtered = df.copy()
        else:
            week_ago = datetime.today() - timedelta(days=7)
            filtered = df[df['Date'] >= week_ago]
        st.dataframe(filtered, use_container_width=True)
        total = filtered['Amount'].sum()
        st.metric("💸 Total Spent", f"₹{total:.2f}")

# Analytics
elif nav=="Analytics":
    st.header("📈 Analytics Dashboard")
    df = load_expenses()
    if df.empty:
        st.info("No data yet. Add or import transactions to see analytics.")
    else:
        months = st.selectbox("Show last N months", [1,3,6,12], index=1)
        ts = get_time_series(freq='D', months=months)
        st.markdown("<div class='form-card'><h4>Spending Trend</h4>", unsafe_allow_html=True)
        fig,ax = plt.subplots(figsize=(8,3))
        if st.session_state["theme"]=="dark":
            fig.patch.set_facecolor('#0B0B0B'); ax.set_facecolor('#0B0B0B'); ax.plot(ts.index, ts.values, color='#00E5FF')
            ax.tick_params(colors='white'); ax.spines['bottom'].set_color('gray'); ax.spines['left'].set_color('gray')
        else:
            fig.patch.set_facecolor('#fff'); ax.set_facecolor('#fff'); ax.plot(ts.index, ts.values, color='#0077b6')
        ax.set_ylabel("₹")
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='form-card'><h4>Category Comparison (last 30 days)</h4>", unsafe_allow_html=True)
        cat30 = category_summary(30)
        if cat30.empty:
            st.info("Not enough category data.")
        else:
            fig2,ax2 = plt.subplots(figsize=(6,3))
            cats = cat30.index[:8]; vals = cat30.values[:8]
            colors = ["#00E5FF","#7C4DFF","#00C853","#FF1744","#FFA726","#FFB74D","#8E24AA","#42A5F5"]
            ax2.barh(cats[::-1], vals[::-1], color=colors[:len(cats)])
            if st.session_state["theme"]=="dark":
                ax2.set_facecolor('#0B0B0B'); fig2.patch.set_facecolor('#0B0B0B'); ax2.tick_params(colors='white')
            st.pyplot(fig2)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='form-card'><h4>Weekday Spending (last 30 days)</h4>", unsafe_allow_html=True)
        heat = daily_heatmap(30)
        if heat is None or heat.sum()==0:
            st.info("No weekday pattern yet.")
        else:
            fig3,ax3 = plt.subplots(figsize=(6,2))
            dow = heat.index; vals = heat.values
            ax3.bar(dow, vals, color="#00E5FF" if st.session_state["theme"]=="dark" else "#0077b6")
            if st.session_state["theme"]=="dark":
                ax3.set_facecolor('#0B0B0B'); fig3.patch.set_facecolor('#0B0B0B'); ax3.tick_params(colors='white')
            st.pyplot(fig3)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='form-card'><h4>Detected Recurring Payments</h4>", unsafe_allow_html=True)
        recs = detect_recurring()
        if not recs:
            st.write("No recurring payments detected.")
        else:
            for r in recs:
                st.write(f"- {r['note']} — {r['count']} times, avg ₹{r['avg']:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

# AI Assistant
elif nav=="AI Assistant":
    st.header("💬 AI Assistant — Ask about your spending")
    st.markdown("Ask in plain English, e.g. *Where am I overspending?*, *How much this month?*, *Any subscriptions?*")
    q = st.text_input("Ask SmartSpends:", key="ai_query")
    if st.button("Ask") and q.strip()!="":
        with st.spinner("Analyzing..."):
            ans = ai_answer(q)
        st.markdown("**Answer:**")
        st.write(ans)
    st.markdown("---")
    st.markdown("<div class='form-card'><h4>Auto Insights (one-click)</h4>", unsafe_allow_html=True)
    if st.button("Generate Insights"):
        with st.spinner("Generating insights..."):
            ins = generate_insights()
        for i in ins:
            st.markdown(f"- {i}")
    st.markdown("</div>", unsafe_allow_html=True)

# Upload Bank CSV
elif nav=="Upload Bank CSV":
    st.header("🏦 Upload Bank Statement (CSV)")
    uploaded_file = st.file_uploader("Choose CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            bdf = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(bdf.head())
            possible_debit_cols = [c for c in bdf.columns if 'debit' in c.lower() or 'withdraw' in c.lower() or 'amount' in c.lower()]
            possible_date_cols = [c for c in bdf.columns if 'date' in c.lower()]
            possible_desc_cols = [c for c in bdf.columns if 'desc' in c.lower() or 'narration' in c.lower() or 'details' in c.lower()]
            debit_col = possible_debit_cols[0] if possible_debit_cols else st.selectbox("Select debit column", bdf.columns)
            date_col = possible_date_cols[0] if possible_date_cols else st.selectbox("Select date column", bdf.columns)
            desc_col = possible_desc_cols[0] if possible_desc_cols else st.selectbox("Select description column", bdf.columns)
            debit_df = bdf[bdf[debit_col].notna()][[date_col, debit_col, desc_col]].copy()
            debit_df.columns = ['Date','Amount','Note']
            debit_df['Category'] = 'Bank Debit'
            debit_df['Date'] = debit_df['Date'].apply(parse_date_flexibly)
            debit_df = debit_df.dropna(subset=['Date'])
            debit_df['Amount'] = debit_df['Amount'].astype(float)
            existing = load_expenses()
            combined = pd.concat([existing, debit_df[['Date','Amount','Category','Note']]], ignore_index=True)
            combined.to_csv(EXPENSE_FILE, index=False)
            st.success(f"Imported {len(debit_df)} debits.")
        except Exception as e:
            st.error(f"Error: {e}")

# Razorpay page
elif nav=="Online Payment (Razorpay)":
    st.header("💳 Razorpay (Test Mode)")
    amount = st.number_input("Amount (₹)", min_value=1.0, step=1.0, format="%.2f")
    category = st.text_input("Category", "Online Payment")
    note = st.text_input("Note", "Razorpay Test")
    if st.button("Create Test Order & Log"):
        try:
            if rclient is None:
                raise Exception("Razorpay client not configured or package missing.")
            order = rclient.order.create({"amount": int(amount*100),"currency":"INR","payment_capture":1})
            st.success("Order created (test).")
            st.json(order)
            add_expense(amount, category, note)
            st.success("Logged to expenses.")
        except Exception as e:
            st.error(f"Error: {e}") 