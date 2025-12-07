# 📊 Personal Expense Tracker (Python CLI Application)

A simple, fast, and colorful **Python Expense Tracker** built using  
✔ Python  
✔ Rich (for a beautiful terminal UI)  
✔ Matplotlib (for charts)  
✔ CSV-based storage (no database needed)

This application helps users track daily expenses, view weekly charts, search records, and set spending limits — all from a clean, modern command-line interface.

---

## 🚀 Features

### ✅ Add New Expenses  
- Automatically captures date  
- Stores amount, category, and optional note  
- Saves everything in `expenses.csv`

---

### 📊 Weekly Expense Pie Chart  
Visualizes where your money went in the last 7 days using a **Matplotlib pie chart**.

---

### 🗓️ Weekly Calendar View  
Displays a breakdown of how much you spent **each day** in the past week.

---

### 🔍 Search Expenses  
Search records by:
- Date → `2025-01-10`  
- Category → `food`, `travel`  
- Keyword → `pizza`, `uber`  

---

### ⚠️ Weekly Spending Limit  
- Set your personal weekly limit  
- Automatically warns you if spending crosses the set limit  
- Uses `limit.txt` to store your limit

---

### 🎨 Rich Terminal UI  
Beautiful CLI using:
- Colors  
- Emojis  
- Styled messages  
- Tables  
- Clean formatting  

---

## 🛠️ Tech Stack

- Python 3  
- Rich  
- Matplotlib  
- CSV storage  

---

## 📦 Installation

#### Clone the repository
```bash
git clone https://github.com/yourusername/expense-tracker.git
cd expense-tracker