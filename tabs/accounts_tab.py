import tkinter as tk
from tkinter import ttk, messagebox
import re
from sqlalchemy.exc import IntegrityError
from db.models import Account, Transaction


class AccountsTab(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self._item_ids = {}  # Map treeview item IDs to account IDs
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # Filter bar
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=4)

        ttk.Label(bar, text="Type:").pack(side="left")
        self.type_var = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self.type_var, values=[
                     "All", "Checking", "Savings", "Cash", "Credit"], width=12, state="readonly").pack(side="left", padx=4)

        ttk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.apply_filters())
        ttk.Entry(bar, textvariable=self.search_var,
                  width=16).pack(side="left", padx=4)

        ttk.Button(bar, text="Apply", command=self.apply_filters).pack(
            side="left", padx=4)

        # Accounts table
        cols = ("Name", "Type", "Balance")
        self.tree = ttk.Treeview(
            self, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("Name", width=200)
        self.tree.column("Type", width=150)
        self.tree.column("Balance", width=150, anchor="e")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # Empty state message
        self.empty_label = ttk.Label(
            self, text="No accounts found", font=("Segoe UI", 11, "italic"), foreground="gray50")

        # Footer sum (computed locally from table rows)
        self.sum_label = ttk.Label(
            self, text="Total Balance: $0.00", anchor="e")
        self.sum_label.pack(fill="x", padx=8, pady=(0, 6))

        # Buttons
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=6, pady=4)
        ttk.Button(buttons, text="Add",
                   command=self.add_account).pack(side="left")
        ttk.Button(buttons, text="Edit", command=self.edit_account).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Refresh", command=self.load_data).pack(
            side="left", padx=4)

    def load_data(self):
        """Load accounts from database."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._item_ids.clear()

        accounts = self.session.query(Account).all()
        for acc in accounts:
            item_id = self.tree.insert("", "end",
                                      values=[acc.name, acc.type, f"{float(acc.balance):,.2f}"])
            self._item_ids[item_id] = acc.id
        self.apply_filters()
        self.refresh_sum()
        self._update_empty_state()

    def apply_filters(self):
        """Apply filters to account list."""
        type_filter = self.type_var.get()
        search_filter = self.search_var.get().lower().strip()

        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            name = values[0].lower()
            acc_type = values[1]

            # Type filter
            if type_filter != "All" and acc_type != type_filter:
                self.tree.detach(item_id)
                continue

            # Search filter
            if search_filter and search_filter not in name:
                self.tree.detach(item_id)
                continue

            # Show item
            if item_id not in self.tree.get_children():
                self.tree.reattach(item_id, "", "end")

        self.refresh_sum()
        self._update_empty_state()

    # helpers
    def _dollar_ok(self, text: str) -> bool:
        return bool(re.fullmatch(r"\$?\d+(\.\d{1,2})?", text.strip()))

    def _selected(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _get_account_id(self, item_id):
        """Get account ID from treeview item ID."""
        return self._item_ids.get(item_id)

    def refresh_sum(self):
        total = 0.0
        for i in self.tree.get_children():
            vals = self.tree.item(i, "values")
            try:
                total += float(vals[2].replace("$", "").replace(",", ""))
            except Exception:
                pass
        self.sum_label.config(text=f"Total Balance: ${total:,.2f}")

    def _update_empty_state(self):
        """Show or hide empty state message based on treeview content."""
        if len(self.tree.get_children()) == 0:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

    # Dialogs/actions
    def add_account(self):
        d = tk.Toplevel(self)
        d.title("Add Account")
        d.geometry("320x160")
        d.resizable(False, False)
        name_var = tk.StringVar()
        type_var = tk.StringVar(value="Checking")
        balance_var = tk.StringVar(value="0.00")

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(
                row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Name", ttk.Entry(d, textvariable=name_var, width=20))
        row(1, "Type", ttk.Combobox(d, textvariable=type_var, values=[
            "Checking", "Savings", "Cash", "Credit"], width=18, state="readonly"))
        row(2, "Balance ($)", ttk.Entry(d, textvariable=balance_var, width=12))

        def save():
            if not name_var.get().strip():
                messagebox.showerror(
                    "Invalid Name", "Account name is required.")
                return
            amt_text = balance_var.get().strip()
            if not self._dollar_ok(amt_text):
                messagebox.showerror(
                    "Invalid Amount", "Enter a valid dollar amount (e.g., 10 or 10.50).")
                return

            try:
                account = Account(
                    name=name_var.get().strip(),
                    type=type_var.get(),
                    balance=float(amt_text.replace("$", ""))
                )
                self.session.add(account)
                self.session.commit()
                self.load_data()
                self.main_window.refresh_all_tabs()
                d.destroy()
            except IntegrityError:
                self.session.rollback()
                messagebox.showerror(
                    "Error", "An account with this name already exists.")
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to save account: {str(e)}")

        button_frame = ttk.Frame(d)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save", command=save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=d.destroy).pack(side="left", padx=5)

    def edit_account(self):
        sel = self._selected()
        if not sel:
            messagebox.showinfo("Edit", "Select an account to edit.")
            return

        acc_id = self._get_account_id(sel)
        if not acc_id:
            return

        account = self.session.query(Account).filter_by(id=acc_id).first()
        if not account:
            return

        item_vals = self.tree.item(sel, "values")

        d = tk.Toplevel(self)
        d.title("Edit Account")
        d.geometry("340x180")
        d.resizable(False, False)
        name_var = tk.StringVar(value=item_vals[0])
        type_var = tk.StringVar(value=item_vals[1])
        balance_var = tk.StringVar(value=str(item_vals[2]))

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(
                row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Name", ttk.Entry(d, textvariable=name_var, width=22))
        row(1, "Type", ttk.Combobox(d, textvariable=type_var, values=[
            "Checking", "Savings", "Cash", "Credit"], width=20, state="readonly"))
        row(2, "Balance ($)", ttk.Entry(d, textvariable=balance_var, width=12))

        def save():
            if not name_var.get().strip():
                messagebox.showerror(
                    "Invalid Name", "Account name is required.")
                return
            amt_text = balance_var.get().strip()
            if not self._dollar_ok(amt_text):
                messagebox.showerror(
                    "Invalid Amount", "Enter a valid dollar amount (e.g., 10 or 10.50).")
                return

            try:
                # Check if name changed and if new name conflicts
                if name_var.get().strip() != account.name:
                    existing = self.session.query(Account).filter_by(
                        name=name_var.get().strip()).first()
                    if existing:
                        messagebox.showerror(
                            "Error", "An account with this name already exists.")
                        return

                account.name = name_var.get().strip()
                account.type = type_var.get()
                account.balance = float(
                    amt_text.replace("$", "").replace(",", ""))
                self.session.commit()
                self.load_data()
                self.main_window.refresh_all_tabs()
                d.destroy()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to update account: {str(e)}")

        button_frame = ttk.Frame(d)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save", command=save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=d.destroy).pack(side="left", padx=5)

    def delete_selected(self):
        selected = self._selected()
        if not selected:
            messagebox.showinfo("Delete", "Select an account to delete.")
            return

        acc_id = self._get_account_id(selected)
        if not acc_id:
            return

        account = self.session.query(Account).filter_by(id=acc_id).first()
        if not account:
            return

        # Check if account is used by transactions
        transaction_count = self.session.query(Transaction).filter_by(
            account_id=acc_id).count()

        if transaction_count > 0:
            messagebox.showerror(
                "Cannot Delete",
                f"This account is used by {transaction_count} transaction(s). "
                "Please delete or update them first.")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete account '{account.name}'?"):
            try:
                self.session.delete(account)
                self.session.commit()
                self.load_data()
                self.main_window.refresh_all_tabs()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to delete account: {str(e)}")

