# src/utils.py
# Shared utilities — password hashing, date parsing, and CSS theme helpers.

import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st

# --------------- Constants ---------------
DEFAULT_THEME = "dark"


# --------------- Password Hashing ---------------

def hash_with_salt(password: str, salt: str) -> str:
    """SHA-256 hash of (salt + password)."""
    return hashlib.sha256((salt + password).encode()).hexdigest()


# --------------- Date Parsing ---------------

def parse_date_flexibly(x):
    """Try multiple date formats and return YYYY-MM-DD or None."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(x).strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    try:
        return pd.to_datetime(x, dayfirst=True, errors="coerce").strftime("%Y-%m-%d")
    except Exception:
        return None


# --------------- CSS Themes ---------------

DARK_CSS = """
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
"""

LIGHT_CSS = """
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
"""


def load_css(theme: str):
    """Inject the appropriate CSS into the Streamlit page."""
    st.markdown(DARK_CSS if theme == "dark" else LIGHT_CSS, unsafe_allow_html=True)


def toggle_theme():
    """Flip between dark and light in session state."""
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
