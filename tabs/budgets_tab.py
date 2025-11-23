import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import re
from sqlalchemy.exc import IntegrityError
from db.models import Category, Transaction, Budget


class BudgetsTab(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self._item_ids = {}  # Map treeview item IDs to budget IDs
        self._build_ui()
        self.load_data()

    def _build_ui(self):
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

        cols = ("Category", "Target", "Spent", "Remaining", "Status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("Category", width=200)
        self.tree.column("Target", width=120, anchor="e")
        self.tree.column("Spent", width=120, anchor="e")
        self.tree.column("Remaining", width=120, anchor="e")
        self.tree.column("Status", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # Empty state message
        self.empty_label = ttk.Label(
            self, text="No budgets found for this month", font=("Segoe UI", 11, "italic"), foreground="gray50")

        # Buttons
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=6, pady=4)
        ttk.Button(buttons, text="Add",
                   command=self.add_budget).pack(side="left")
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Refresh", command=self.load_data).pack(
            side="left", padx=4)

        # inline edit for "Target" on double-click
        self.tree.bind("<Double-1>", self._edit_target_cell)

    def load_data(self):
        """Load budgets for selected month/year and calculate spent/remaining."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._item_ids.clear()

        try:
            month = int(self.month_var.get())
            year = int(self.year_var.get())
        except:
            return

        # Get budgets for this month/year
        budgets = self.session.query(Budget).filter(
            Budget.month == month,
            Budget.year == year
        ).all()

        # Date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        for budget in budgets:
            category = self.session.query(Category).filter_by(
                id=budget.category_id).first()
            if not category:
                continue

            # Calculate spent (only posted transactions)
            transactions = self.session.query(Transaction).filter(
                Transaction.category_id == budget.category_id,
                Transaction.date >= start_date,
                Transaction.date < end_date,
                Transaction.planned == False
            ).all()

            spent = sum(float(t.amount) for t in transactions)
            target = float(budget.target_amount)
            remaining = target - spent
            status = "Over" if remaining < 0 else "OK"

            item_id = self.tree.insert("", "end",
                                      values=[
                                          category.name,
                                          f"{target:,.2f}",
                                          f"{spent:,.2f}",
                                          f"{remaining:,.2f}",
                                          status
                                      ])
            self._item_ids[item_id] = budget.id
        
        self._update_empty_state()

    def _edit_target_cell(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        col = self.tree.identify_column(event.x)
        if col != "#2":  # Target column
            return
        item = sel[0]
        x, y, w, h = self.tree.bbox(item, col)
        entry = ttk.Entry(self.tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, self.tree.item(item, "values")[1])
        entry.focus()

        def save_edit(e=None):
            val = entry.get().strip()
            if not re.fullmatch(r"\$?\d+(\.\d{1,2})?", val):
                entry.destroy()
                return

            budget_id = self._item_ids.get(item)
            if not budget_id:
                entry.destroy()
                return

            try:
                budget = self.session.query(
                    Budget).filter_by(id=budget_id).first()
                if not budget:
                    entry.destroy()
                    return

                target = float(val.replace("$", "").replace(",", ""))
                budget.target_amount = target
                self.session.commit()

                self.load_data()
                self.main_window.update_status_bar()
                entry.destroy()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to update budget: {str(e)}")
                entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def _update_empty_state(self):
        """Show or hide empty state message based on treeview content."""
        if len(self.tree.get_children()) == 0:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

    def add_budget(self):
        """Add a new budget."""
        categories = self.session.query(Category).all()
        if not categories:
            messagebox.showinfo(
                "No Categories", "Please create categories first.")
            return

        d = tk.Toplevel(self)
        d.title("Add Budget")
        d.geometry("320x180")
        d.resizable(False, False)

        category_var = tk.StringVar()
        target_var = tk.StringVar()

        try:
            month = int(self.month_var.get())
            year = int(self.year_var.get())
        except:
            messagebox.showerror("Error", "Invalid month/year.")
            d.destroy()
            return

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(
                row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        category_names = [cat.name for cat in categories]
        row(0, "Category", ttk.Combobox(d, textvariable=category_var,
                                        values=category_names, width=18, state="readonly"))
        row(1, "Target ($)", ttk.Entry(d, textvariable=target_var, width=12))

        def save():
            if not category_var.get().strip():
                messagebox.showerror("Error", "Please select a category.")
                return

            target_text = target_var.get().strip()
            if not re.fullmatch(r"\$?\d+(\.\d{1,2})?", target_text):
                messagebox.showerror("Error", "Enter a valid dollar amount.")
                return

            try:
                category = self.session.query(Category).filter_by(
                    name=category_var.get().strip()).first()
                if not category:
                    messagebox.showerror("Error", "Invalid category.")
                    return

                # Check if budget already exists
                existing = self.session.query(Budget).filter_by(
                    category_id=category.id,
                    month=month,
                    year=year
                ).first()

                if existing:
                    messagebox.showerror(
                        "Error", "A budget for this category and month already exists.")
                    return

                target = float(target_text.replace("$", "").replace(",", ""))
                budget = Budget(
                    category_id=category.id,
                    month=month,
                    year=year,
                    target_amount=target
                )

                self.session.add(budget)
                self.session.commit()

                self.load_data()
                self.main_window.update_status_bar()
                d.destroy()
            except IntegrityError:
                self.session.rollback()
                messagebox.showerror(
                    "Error", "A budget for this category and month already exists.")
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to save budget: {str(e)}")

        button_frame = ttk.Frame(d)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save", command=save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=d.destroy).pack(side="left", padx=5)

    def delete_selected(self):
        """Delete selected budget."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select a budget to delete.")
            return

        budget_id = self._item_ids.get(sel[0])
        if not budget_id:
            return

        budget = self.session.query(Budget).filter_by(id=budget_id).first()
        if not budget:
            return

        category = self.session.query(Category).filter_by(
            id=budget.category_id).first()
        category_name = category.name if category else "Unknown"

        if messagebox.askyesno("Confirm Delete", f"Delete budget for '{category_name}'?"):
            try:
                self.session.delete(budget)
                self.session.commit()
                self.load_data()
                self.main_window.update_status_bar()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to delete budget: {str(e)}")

