# Personal Budgeting Application

## Why

Financial literacy is understudied in today's day and age, and it should be vital for us to know and fully understand, with the core part of financial literacy being knowing where your money is truly going. This application helps young people track and manage their finances by providing a simple, organized way to monitor transactions and budgets in one place.

## Project Overview

This is a personal budgeting application built with Python and Tkinter that lets users track and manage their transactions and budgets. The app provides real-time financial tracking with an intuitive interface designed for clarity and simplicity.

### Key Features

**Transactions Tab:**

- Add, edit, and delete transactions with automatic total calculations
- Filter transactions by month, year, account, category, and search terms
- Mark transactions as planned or posted for better budget tracking
- View running totals and transaction summaries

**Budgets Tab:**

- Create and manage budget targets for each category
- Track actual spending against planned budgets
- Visual status indicators showing if spending is over or within budget
- Quick inline editing of budget targets
- Automatic calculations of remaining budget

**Accounts Tab:**

- Create and manage multiple accounts (Checking, Savings, Cash, Credit)
- Track account balances
- View total balance across all accounts
- Filter accounts by type and search

**Categories Tab:**

- Create and manage transaction categories (Income/Expense)
- Organize categories with descriptions
- Filter categories by type and search

**General Features:**

- Real-time status bar showing current month spending, planned amounts, and budget alarms
- Cross-tab integration with automatic updates
- Data persistence with SQLite database
- Account balance updates when transactions are posted (not planned)
- Input validation for all financial entries

## Technical Implementation

The application uses:

- **Frontend:** Tkinter for UI components
- **Backend:** SQLAlchemy ORM for database management
- **Database:** SQLite for data persistence
- **Architecture:** Modular design with separate tab classes for maintainability

## Authors

- Sarthak Sethi
- Satyansh Rai

## How to Run the application

1. **Enter terminal**

2. **CD/Locate to project folder**

3. **Install dependencies** (if needed)
   `pip install -r requirements.txt`

4. **Starting the application**
   `python app.py`

5. **Application is now ready**

## How to Use the application itself

### Getting Started

**Step 1: Set up Accounts**

- Go to the Accounts tab
- Click "Add" to create your first account (Checking, Savings, Cash, or Credit)
- Enter account name, type, and starting balance
- You can create multiple accounts to track different sources of money

**Step 2: Create Categories**

- Go to the Categories tab
- Click "Add" to create transaction categories
- Choose between Income or Expense type
- Add a description to help organize your spending
- Common categories: Groceries, Rent, Salary, Entertainment, etc.

**Step 3: Add Transactions**

- Go to the Transactions tab
- Click "Add" to record a new transaction
- Select date, account, category, payee, amount, and add notes
- Mark as "Planned" for future transactions or "Posted" for completed ones
- Posted transactions automatically update account balances

**Step 4: Set Budgets**

- Go to the Budgets tab
- Select the month and year you want to budget for
- Click "Add" to set a budget target for a category
- Double-click on the Target column to quickly edit budget amounts
- View your spending vs. budget with status indicators (OK/Over)

### Tips for Effective Use

- **Filtering**: Use the filter bars in each tab to quickly find specific transactions, accounts, or categories
- **Search**: Type in the search box to filter by name, payee, or notes
- **Status Bar**: Check the bottom status bar for quick overview of month spending, planned amounts, and budget alarms
- **Refresh**: Click the Refresh button in any tab to reload data from the database
- **Planned vs Posted**: Planned transactions appear in gray italic text and don't affect account balances until marked as posted
