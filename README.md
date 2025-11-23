# Personal Budgeting Application

## Why

Financial literacy is understudied in today's day and age, and it should be vital for us to know and fully understand, with the core part of financial literacy being knowing where your money is truly going. This application helps young people track and manage their finances by providing a simple, organized way to monitor transactions and budgets in one place.

## Project Overview

My Budget Hero is a personal budgeting application built with Python and Tkinter that lets users track and manage their transactions and budgets. The app provides real-time financial tracking with an intuitive interface designed for clarity and simplicity.

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
