import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import re
from utils import make_date_triple
from db.models import Account, Category, Transaction


class TransactionsTab(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self._item_ids = {}  # Map treeview item IDs to transaction IDs
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # Filter bar
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=4)

        ttk.Label(bar, text="Month:").pack(side="left")
        months = [f"{i:02d}" for i in range(1, 13)]
        self.month_var = tk.StringVar(value=datetime.now().strftime("%m"))
        self.month_var.trace_add("write", lambda *_: self.load_data())
        ttk.Combobox(bar, textvariable=self.month_var, values=months,
                     width=4, state="readonly").pack(side="left", padx=2)

        years = [str(y) for y in range(
            datetime.now().year - 5, datetime.now().year + 6)]
        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        self.year_var.trace_add("write", lambda *_: self.load_data())
        ttk.Combobox(bar, textvariable=self.year_var, values=years,
                     width=6, state="readonly").pack(side="left", padx=2)

        ttk.Label(bar, text="Account:").pack(side="left")
        self.account_var = tk.StringVar(value="All")
        self.account_combo = ttk.Combobox(bar, textvariable=self.account_var,
                                          width=12, state="readonly")
        self.account_combo.pack(side="left", padx=4)

        ttk.Label(bar, text="Category:").pack(side="left")
        self.cat_var = tk.StringVar(value="All")
        self.cat_combo = ttk.Combobox(bar, textvariable=self.cat_var,
                                      width=12, state="readonly")
        self.cat_combo.pack(side="left", padx=4)

        ttk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.apply_filters())
        ttk.Entry(bar, textvariable=self.search_var,
                  width=16).pack(side="left", padx=4)

        ttk.Label(bar, text="Show:").pack(side="left")
        self.show_var = tk.StringVar(value="Both")
        ttk.Combobox(bar, textvariable=self.show_var, values=[
                     "Posted", "Planned", "Both"], width=10, state="readonly").pack(side="left", padx=4)

        ttk.Button(bar, text="Apply", command=self.apply_filters).pack(
            side="left", padx=4)
        ttk.Button(bar, text="Refresh", command=self.load_data).pack(
            side="left", padx=4)

        # Transactions table
        cols = ("Date", "Account", "Category",
                "Payee", "Amount", "Note", "Planned?")
        self.tree = ttk.Treeview(
            self, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("Date", width=100)
        self.tree.column("Account", width=120)
        self.tree.column("Category", width=120)
        self.tree.column("Payee", width=140)
        self.tree.column("Amount", width=100, anchor="e")
        self.tree.column("Note", width=120)
        self.tree.column("Planned?", width=80, anchor="center")
        self.tree.tag_configure(
            "planned", foreground="gray40", font=("Segoe UI", 10, "italic"))
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # Footer sum (computed locally from table rows)
        self.sum_label = ttk.Label(self, text="Sum: $0.00", anchor="e")
        self.sum_label.pack(fill="x", padx=8, pady=(0, 6))

        # Buttons
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=6, pady=4)
        ttk.Button(buttons, text="Add",
                   command=self.add_transaction).pack(side="left")
        ttk.Button(buttons, text="Edit", command=self.edit_transaction).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Refresh", command=self.load_data).pack(
            side="left", padx=4)

    def update_dropdowns(self):
        """Update account and category dropdowns from database."""
        accounts = self.session.query(Account).all()
        account_names = ["All"] + [acc.name for acc in accounts]
        self.account_combo["values"] = account_names

        categories = self.session.query(Category).all()
        category_names = ["All"] + [cat.name for cat in categories]
        self.cat_combo["values"] = category_names

    def load_data(self):
        """Load transactions from database."""
        self.update_dropdowns()

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._item_ids.clear()

        # Get filter values
        month = int(self.month_var.get())
        year = int(self.year_var.get())

        # Date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        transactions = self.session.query(Transaction).filter(
            Transaction.date >= start_date,
            Transaction.date < end_date
        ).order_by(Transaction.date.desc()).all()

        for txn in transactions:
            account = self.session.query(Account).filter_by(
                id=txn.account_id).first()
            category = self.session.query(Category).filter_by(
                id=txn.category_id).first()

            account_name = account.name if account else "Unknown"
            category_name = category.name if category else "Unknown"

            item_id = self.tree.insert("", "end",
                                       values=[
                                           txn.date.isoformat(),
                                           account_name,
                                           category_name,
                                           txn.payee or "",
                                           f"{float(txn.amount):,.2f}",
                                           txn.note or "",
                                           "Yes" if txn.planned else "No"
                                       ],
                                       tags=("planned",) if txn.planned else ())
            self._item_ids[item_id] = txn.id

        self.apply_filters()

    def apply_filters(self):
        """Apply filters to transaction list."""
        account_filter = self.account_var.get()
        category_filter = self.cat_var.get()
        search_filter = self.search_var.get().lower().strip()
        show_filter = self.show_var.get()

        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            account_name = values[1]
            category_name = values[2]
            payee = (values[3] or "").lower()
            note = (values[5] or "").lower()
            is_planned = values[6] == "Yes"

            # Account filter
            if account_filter != "All" and account_name != account_filter:
                self.tree.detach(item_id)
                continue

            # Category filter
            if category_filter != "All" and category_name != category_filter:
                self.tree.detach(item_id)
                continue

            # Show filter
            if show_filter == "Posted" and is_planned:
                self.tree.detach(item_id)
                continue
            if show_filter == "Planned" and not is_planned:
                self.tree.detach(item_id)
                continue

            # Search filter
            if search_filter:
                if (search_filter not in payee and
                    search_filter not in note and
                    search_filter not in account_name.lower() and
                        search_filter not in category_name.lower()):
                    self.tree.detach(item_id)
                    continue

            # Show item
            if item_id not in self.tree.get_children():
                self.tree.reattach(item_id, "", "end")

        self.refresh_sum()

    # helpers
    def _dollar_ok(self, text: str) -> bool:
        return bool(re.fullmatch(r"\$?\d+(\.\d{1,2})?", text.strip()))

    def _selected(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _get_transaction_id(self, item_id):
        """Get transaction ID from treeview item ID."""
        return self._item_ids.get(item_id)

    def refresh_sum(self):
        total = 0.0
        for i in self.tree.get_children():
            vals = self.tree.item(i, "values")
            try:
                total += float(vals[4].replace(",", ""))
            except Exception:
                pass
        self.sum_label.config(text=f"Sum: ${total:,.2f}")

    def _update_account_balance(self, account_id, amount, category_id, is_planned):
        """Update account balance when transaction is posted (not planned)."""
        if is_planned:
            return

        account = self.session.query(Account).filter_by(id=account_id).first()
        category = self.session.query(
            Category).filter_by(id=category_id).first()

        if account and category:
            # Income increases balance, Expense decreases balance
            if category.type == "Income":
                account.balance = float(account.balance) + amount
            else:  # Expense
                account.balance = float(account.balance) - amount
            self.session.commit()

    # Dialogs/actions
    def add_transaction(self):
        self.update_dropdowns()

        d = tk.Toplevel(self)
        d.title("Add Transaction")
        d.geometry("360x300")
        d.resizable(False, False)
        date_var = tk.StringVar(value=date.today().isoformat())
        account_var = tk.StringVar()
        category_var = tk.StringVar()
        payee_var = tk.StringVar()
        amount_var = tk.StringVar()
        note_var = tk.StringVar()
        planned_var = tk.StringVar(value="No")

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(
                row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Date", make_date_triple(d, date_var))

        accounts = self.session.query(Account).all()
        account_names = [acc.name for acc in accounts]
        account_combo = ttk.Combobox(d, textvariable=account_var,
                                     values=account_names, width=18, state="readonly")
        row(1, "Account", account_combo)

        categories = self.session.query(Category).all()
        category_names = [cat.name for cat in categories]
        category_combo = ttk.Combobox(d, textvariable=category_var,
                                      values=category_names, width=18, state="readonly")
        row(2, "Category", category_combo)

        row(3, "Payee", ttk.Entry(d, textvariable=payee_var, width=20))
        row(4, "$ Amount", ttk.Entry(d, textvariable=amount_var, width=12))
        row(5, "Note", ttk.Entry(d, textvariable=note_var, width=25))
        row(6, "Planned?", ttk.Combobox(d, textvariable=planned_var,
            values=["Yes", "No"], width=8, state="readonly"))

        def save():
            if not account_var.get().strip():
                messagebox.showerror("Error", "Please select an account.")
                return
            if not category_var.get().strip():
                messagebox.showerror("Error", "Please select a category.")
                return

            amt_text = amount_var.get().strip()
            if not self._dollar_ok(amt_text):
                messagebox.showerror(
                    "Invalid Amount", "Enter a valid dollar amount (e.g., 10 or 10.50).")
                return

            try:
                # Get account and category IDs
                account = self.session.query(Account).filter_by(
                    name=account_var.get().strip()).first()
                category = self.session.query(Category).filter_by(
                    name=category_var.get().strip()).first()

                if not account or not category:
                    messagebox.showerror(
                        "Error", "Invalid account or category.")
                    return

                # Parse date
                try:
                    txn_date = date.fromisoformat(date_var.get())
                except (ValueError, AttributeError):
                    messagebox.showerror("Error", "Invalid date format.")
                    return

                amount = float(amt_text.replace("$", ""))
                planned = (planned_var.get() == "Yes")

                transaction = Transaction(
                    date=txn_date,
                    account_id=account.id,
                    category_id=category.id,
                    payee=payee_var.get().strip() or None,
                    amount=amount,
                    note=note_var.get().strip() or None,
                    planned=planned
                )

                self.session.add(transaction)
                self.session.commit()

                # Update account balance if not planned
                self._update_account_balance(
                    account.id, amount, category.id, planned)

                self.load_data()
                self.main_window.refresh_all_tabs()
                d.destroy()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to save transaction: {str(e)}")

        button_frame = ttk.Frame(d)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save",
                   command=save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=d.destroy).pack(side="left", padx=5)

    def edit_transaction(self):
        sel = self._selected()
        if not sel:
            messagebox.showinfo("Edit", "Select a transaction to edit.")
            return

        txn_id = self._get_transaction_id(sel)
        if not txn_id:
            return

        transaction = self.session.query(
            Transaction).filter_by(id=txn_id).first()
        if not transaction:
            return

        account = self.session.query(Account).filter_by(
            id=transaction.account_id).first()
        category = self.session.query(Category).filter_by(
            id=transaction.category_id).first()

        self.update_dropdowns()

        d = tk.Toplevel(self)
        d.title("Edit Transaction")
        d.geometry("340x360")
        d.resizable(False, False)
        date_var = tk.StringVar(value=transaction.date.isoformat())
        account_var = tk.StringVar(value=account.name if account else "")
        category_var = tk.StringVar(value=category.name if category else "")
        payee_var = tk.StringVar(value=transaction.payee or "")
        amount_var = tk.StringVar(value=str(transaction.amount))
        note_var = tk.StringVar(value=transaction.note or "")
        planned_var = tk.StringVar(
            value="Yes" if transaction.planned else "No")

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(
                row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Date", make_date_triple(d, date_var))

        accounts = self.session.query(Account).all()
        account_names = [acc.name for acc in accounts]
        account_combo = ttk.Combobox(d, textvariable=account_var,
                                     values=account_names, width=20, state="readonly")
        row(1, "Account", account_combo)

        categories = self.session.query(Category).all()
        category_names = [cat.name for cat in categories]
        category_combo = ttk.Combobox(d, textvariable=category_var,
                                      values=category_names, width=20, state="readonly")
        row(2, "Category", category_combo)

        row(3, "Payee", ttk.Entry(d, textvariable=payee_var, width=22))
        row(4, "Amount ($)", ttk.Entry(d, textvariable=amount_var, width=12))
        row(5, "Note", ttk.Entry(d, textvariable=note_var, width=22))
        row(6, "Planned?", ttk.Combobox(d, textvariable=planned_var,
            values=["Yes", "No"], width=8, state="readonly"))

        def save():
            if not account_var.get().strip():
                messagebox.showerror("Error", "Please select an account.")
                return
            if not category_var.get().strip():
                messagebox.showerror("Error", "Please select a category.")
                return

            amt_text = amount_var.get().strip()
            if not self._dollar_ok(amt_text):
                messagebox.showerror(
                    "Invalid Amount", "Enter a valid dollar amount (ex: 10, 20, 39.67).")
                return

            try:
                # Get account and category IDs
                account = self.session.query(Account).filter_by(
                    name=account_var.get().strip()).first()
                category = self.session.query(Category).filter_by(
                    name=category_var.get().strip()).first()

                if not account or not category:
                    messagebox.showerror(
                        "Error", "Invalid account or category.")
                    return

                # Parse date
                try:
                    txn_date = date.fromisoformat(date_var.get())
                except (ValueError, AttributeError):
                    messagebox.showerror("Error", "Invalid date format.")
                    return

                amount = float(amt_text.replace("$", ""))
                planned = (planned_var.get() == "Yes")

                # Update account balance if status changed
                old_amount = float(transaction.amount)
                old_planned = transaction.planned
                old_account_id = transaction.account_id
                old_category_id = transaction.category_id

                # Reverse old transaction effect on old account (if it was posted)
                if not old_planned:
                    # Reverse: use negative amount to undo the original transaction
                    self._update_account_balance(
                        old_account_id, -old_amount, old_category_id, False)

                # Update transaction
                transaction.date = txn_date
                transaction.account_id = account.id
                transaction.category_id = category.id
                transaction.payee = payee_var.get().strip() or None
                transaction.amount = amount
                transaction.note = note_var.get().strip() or None
                transaction.planned = planned

                self.session.commit()

                # Apply new transaction effect on new account (if it's posted)
                if not planned:
                    self._update_account_balance(
                        account.id, amount, category.id, False)

                self.load_data()
                self.main_window.refresh_all_tabs()
                d.destroy()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to update transaction: {str(e)}")

        button_frame = ttk.Frame(d)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save",
                   command=save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=d.destroy).pack(side="left", padx=5)

    def delete_selected(self):
        selected = self._selected()
        if not selected:
            return

        txn_id = self._get_transaction_id(selected)
        if not txn_id:
            return

        transaction = self.session.query(
            Transaction).filter_by(id=txn_id).first()
        if not transaction:
            return

        if messagebox.askyesno("Confirm Delete", "Delete this transaction?"):
            try:
                # Update account balance if not planned (reverse the transaction)
                if not transaction.planned:
                    # Reverse: use negative amount to undo the original transaction
                    self._update_account_balance(
                        transaction.account_id, -float(transaction.amount), transaction.category_id, False)

                self.session.delete(transaction)
                self.session.commit()
                self.load_data()
                self.main_window.refresh_all_tabs()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to delete transaction: {str(e)}")
