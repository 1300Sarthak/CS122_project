import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
from db import init_db, get_session, close_session
from db.models import Transaction, Budget
from tabs.categories_tab import CategoriesTab
from tabs.accounts_tab import AccountsTab
from tabs.transactions_tab import TransactionsTab
from tabs.budgets_tab import BudgetsTab


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Budgeting Application")
        self.geometry("1000x650")

        # Initialize database
        init_db()
        self.session = get_session()

        self._build_ui()
        self.update_status_bar()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _build_ui(self):
        # Tabs
        nb = ttk.Notebook(self)
        self.tx_tab = TransactionsTab(nb, self)
        self.bd_tab = BudgetsTab(nb, self)
        self.cat_tab = CategoriesTab(nb, self)
        self.acc_tab = AccountsTab(nb, self)
        nb.add(self.tx_tab, text="Transactions")
        nb.add(self.bd_tab, text="Budgets")
        nb.add(self.cat_tab, text="Categories")
        nb.add(self.acc_tab, text="Accounts")
        nb.pack(fill="both", expand=True)

        # Status bar
        self.status = ttk.Label(
            self, text="Month Spend: $0.00 | Planned: $0.00 | Alarms: 0", anchor="w"
        )
        self.status.pack(fill="x", side="bottom")

    def update_status_bar(self):
        """Update status bar with current month spend, planned amount, and alarms."""
        try:
            now = datetime.now()
            current_month = now.month
            current_year = now.year

            # Calculate month spend (posted transactions only)
            posted_transactions = self.session.query(Transaction).filter(
                Transaction.date >= date(current_year, current_month, 1),
                Transaction.date < date(
                    current_year, current_month + 1, 1) if current_month < 12 else date(current_year + 1, 1, 1),
                Transaction.planned == False
            ).all()

            month_spend = sum(float(t.amount) for t in posted_transactions)

            # Calculate planned amount
            planned_transactions = self.session.query(Transaction).filter(
                Transaction.planned == True
            ).all()

            planned_total = sum(float(t.amount) for t in planned_transactions)

            # Count alarms (budgets over target)
            budgets = self.session.query(Budget).filter(
                Budget.month == current_month,
                Budget.year == current_year
            ).all()

            alarms = 0
            for budget in budgets:
                # Calculate spent for this category in this month
                transactions = self.session.query(Transaction).filter(
                    Transaction.category_id == budget.category_id,
                    Transaction.date >= date(budget.year, budget.month, 1),
                    Transaction.date < date(
                        budget.year, budget.month + 1, 1) if budget.month < 12 else date(budget.year + 1, 1, 1),
                    Transaction.planned == False
                ).all()

                spent = sum(float(t.amount) for t in transactions)
                if spent > float(budget.target_amount):
                    alarms += 1

            self.status.config(
                text=f"Month Spend: ${month_spend:,.2f} | Planned: ${planned_total:,.2f} | Alarms: {alarms}"
            )
        except Exception as e:
            self.status.config(text=f"Error updating status: {str(e)}")

    def refresh_all_tabs(self):
        """Refresh all tabs when data changes."""
        self.cat_tab.load_data()
        self.acc_tab.load_data()
        self.tx_tab.load_data()
        self.bd_tab.load_data()
        self.update_status_bar()

    def on_closing(self):
        """Handle window close event."""
        close_session()
        self.destroy()


if __name__ == "__main__":
    MainWindow().mainloop()
