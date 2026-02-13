# SmartSpends

**Personal finance, but smarter.** A multi-user expense tracking web app with analytics dashboards, an AI assistant, bank statement import, and Razorpay payment integration — built with Python and Streamlit.

---

## Features

### Core Tracking
- **Multi-user authentication** — Register/login with salted SHA-256 password hashing; isolated per-user data
- **Expense management** — Add expenses with amount, category, note, and custom date
- **Weekly spending limits** — Set a personal weekly budget and track remaining balance
- **Bank CSV import** — Upload bank statements; auto-detects date, debit, and description columns

### Analytics Dashboard
- **Spending trend** — Daily spending line chart over 1 / 3 / 6 / 12 months
- **Category breakdown** — Horizontal bar chart of top spending categories (last 30 days)
- **Weekday patterns** — Bar chart showing which days of the week you spend most
- **Recurring charges** — Auto-detects repeated payments (subscriptions, memberships, etc.)
- **Auto-generated insights** — One-click summary: top category %, week-over-week change, large transactions

### AI Assistant
- Ask questions in plain English: *"Where am I overspending?"*, *"How much this month?"*, *"Any subscriptions?"*
- Returns data-driven answers using your real expense history

### Payments & Extras
- **Razorpay integration** — Create test payment orders and auto-log them as expenses
- **Dark / Light theme** — Toggle between polished dark and clean light UI
- **Chart export** — Analytics charts auto-save to `reports/` as PNG files
- **Demo mode** — One-click guest login to explore the app instantly

---

## Screenshots

> Add your screenshots to a `screenshots/` folder and uncomment the lines below.

<!--
![Login Screen](screenshots/login.png)
![Home Dashboard](screenshots/home.png)
![Analytics Dashboard](screenshots/analytics.png)
![AI Assistant](screenshots/ai_assistant.png)
-->

| Page | Description |
|------|-------------|
| **Login / Register** | Tabbed auth screen with demo guest access |
| **Home** | Greeting, weekly stats cards, quick insights |
| **Add Expense** | Form with amount, category, note, date picker |
| **View Summary** | Filterable expense table with total metric |
| **Analytics** | Spending trend, category bars, weekday chart, recurring detection |
| **AI Assistant** | Natural-language Q&A about your spending |
| **Upload Bank CSV** | Drag-and-drop CSV import with auto column detection |
| **Razorpay** | Test payment order creation and auto-logging |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | [Streamlit](https://streamlit.io/) — interactive Python web framework |
| **Data processing** | [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/) |
| **Visualizations** | [Matplotlib](https://matplotlib.org/) |
| **Payments** | [Razorpay Python SDK](https://github.com/razorpay/razorpay-python) (test mode) |
| **Auth** | SHA-256 with per-user random salt (stdlib `hashlib` + `secrets`) |
| **Storage** | Flat files — CSV for expenses, JSON for users, TXT for limits |
| **Language** | Python 3.9+ |

---

## Project Structure

```
smartspends/
├── app.py                  # Streamlit entry point — UI rendering & page routing
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── .gitignore
│
├── src/                    # Core application logic (4 modules)
│   ├── storage.py          #   File paths, directory setup, all CSV/JSON/TXT I/O
│   ├── utils.py            #   Password hashing, date parsing, CSS themes
│   ├── tracker.py          #   Auth (register/verify), expense ops, Razorpay
│   └── analytics.py        #   Trends, categories, recurring, insights, AI Q&A
│
├── data/                   # Runtime user data (gitignored, auto-created)
│   ├── users.json          #   Registered accounts
│   ├── expenses_*.csv      #   Per-user expense records
│   └── limit_*.txt         #   Per-user weekly limits
│
├── reports/                # Auto-saved chart PNGs from Analytics page
│
├── tests/                  # Unit test suite (35 tests)
│   ├── test_utils.py       #   Hashing, date parsing
│   ├── test_storage.py     #   CSV & limit file I/O
│   ├── test_tracker.py     #   Auth flow, expense operations
│   └── test_analytics.py   #   Category summary, recurring, insights, AI
│
└── legacy/
    └── hello.py            # Original single-user prototype (archived)
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip

### Steps

1. **Clone the repository**

```bash
git clone https://github.com/your-username/smartspends.git
cd smartspends
```

2. **Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **(Optional) Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your Razorpay keys if you want payment integration
```

---

## Usage

### Run the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

### Quick start

1. Click **"Use Demo (guest)"** on the login screen to explore with sample data
2. Or **Register** a new account to start fresh
3. Navigate pages via the sidebar: Home, Add Expense, Analytics, AI Assistant, etc.

### Run tests

```bash
python -m unittest discover -s tests -v
```

All 35 tests should pass:

```
test_utils     —  9 tests (hashing, date parsing)
test_storage   —  5 tests (CSV I/O, limit files)
test_tracker   — 10 tests (auth, expense operations)
test_analytics — 11 tests (categories, recurring, insights, AI)
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RAZORPAY_KEY_ID` | Razorpay API key ID | Test key (built-in) |
| `RAZORPAY_KEY_SECRET` | Razorpay API key secret | Test key (built-in) |

The app works out of the box with built-in Razorpay test keys. Set your own in a `.env` file for production use.

---

## Module Overview

| Module | Responsibility | Dependencies |
|--------|---------------|-------------|
| `utils.py` | Password hashing, date format parsing, CSS themes | *standalone* |
| `storage.py` | All file I/O — paths, users JSON, expense CSV, limit TXT | *standalone* |
| `tracker.py` | Auth logic, expense business rules, Razorpay integration | `storage`, `utils` |
| `analytics.py` | Time series, categories, recurring detection, insights, AI Q&A, chart export | `storage` |

Zero circular imports. `utils` and `storage` are leaf modules with no internal dependencies.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run the test suite (`python -m unittest discover -s tests -v`)
5. Commit and push (`git push origin feature/your-feature`)
6. Open a Pull Request

---

## License

This project is open-source and available under the [MIT License](LICENSE).

---

## Author

Built by **Pratham** -- 2025
