import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import calendar
import re

# Helper function that makes it so choosing a date in add or edit transactions is done efficiently with the dropdown.
def make_date_triple(parent, text):
    frm = ttk.Frame(parent)

    def _parse_iso(s):
        try:
            y, m, d = s.split("-")
            return int(y), int(m), int(d)
        except Exception:
            today = date.today()
            return today.year, today.month, today.day

    y0, m0, d0 = _parse_iso(text.get() or "")

    months = [f"{i:02d}" for i in range(1, 13)]
    years = [str(y) for y in range(y0 - 5, y0 + 6)]

    m_var = tk.StringVar(value=f"{m0:02d}")
    d_var = tk.StringVar(value=f"{d0:02d}")
    y_var = tk.StringVar(value=str(y0))

    m_cb = ttk.Combobox(frm, textvariable=m_var, values=months, width=4, state="readonly")
    d_cb = ttk.Combobox(frm, textvariable=d_var, width=4, state="readonly")
    y_cb = ttk.Combobox(frm, textvariable=y_var, values=years, width=6, state="readonly")

    m_cb.pack(side="left")
    ttk.Label(frm, text="/").pack(side="left")
    d_cb.pack(side="left")
    ttk.Label(frm, text="/").pack(side="left")
    y_cb.pack(side="left")

    def _sync_days():
        y = int(y_var.get())
        m = int(m_var.get())
        max_day = calendar.monthrange(y, m)[1]
        vals = [f"{i:02d}" for i in range(1, max_day + 1)]
        d_cb["values"] = vals
        if int(d_var.get()) > max_day:
            d_var.set(f"{max_day:02d}")

    def _sync_iso(*_):
        text.set(f"{int(y_var.get()):04d}-{int(m_var.get()):02d}-{int(d_var.get()):02d}")

    for v in (m_var, y_var):
        v.trace_add("write", lambda *_: (_sync_days(), _sync_iso()))
    d_var.trace_add("write", _sync_iso)

    _sync_days()
    _sync_iso()

    return frm

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My Budget Hero")
        self.geometry("1000x650")
        self._build_ui()

    def _build_ui(self):
        # Tabs
        nb = ttk.Notebook(self)
        self.tx_tab = TransactionsTab(nb)
        self.bd_tab = BudgetsTab(nb)
        self.cat_tab = SimpleTab(nb, "Categories")
        self.acc_tab = SimpleTab(nb, "Accounts")
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

class SimpleTab(ttk.Frame):
    def __init__(self, parent, name):
        super().__init__(parent)
        ttk.Label(self, text=f"{name} tab", font=("Segoe UI", 12, "italic")).pack(pady=40)

def _noop_refresh():
    messagebox.showinfo("Refresh", "Filters applied.")

class TransactionsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._showing_planned_only = False
        self._build_ui()

    def _build_ui(self):
        # Filter bar
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=4)

        ttk.Label(bar, text="Month:").pack(side="left")
        months = [f"{i:02d}" for i in range(1, 13)]
        self.month_var = tk.StringVar(value=datetime.now().strftime("%m"))
        ttk.Combobox(bar, textvariable=self.month_var, values=months, width=4, state="readonly").pack(side="left", padx=2)

        years = [str(y) for y in range(datetime.now().year - 5, datetime.now().year + 6)]
        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        ttk.Combobox(bar, textvariable=self.year_var, values=years, width=6, state="readonly").pack(side="left", padx=2)

        ttk.Label(bar, text="Account:").pack(side="left")
        self.account_var = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self.account_var, values=["All", "Checking", "Cash"], width=12, state="readonly").pack(side="left", padx=4)

        ttk.Label(bar, text="Category:").pack(side="left")
        self.cat_var = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self.cat_var, values=["All", "Groceries", "Rent"], width=12, state="readonly").pack(side="left", padx=4)

        ttk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.search_var, width=16).pack(side="left", padx=4)

        ttk.Label(bar, text="Show:").pack(side="left")
        self.show_var = tk.StringVar(value="Both")
        ttk.Combobox(bar, textvariable=self.show_var, values=["Posted", "Planned", "Both"], width=10, state="readonly").pack(side="left", padx=4)

        ttk.Button(bar, text="Apply", command=_noop_refresh).pack(side="left", padx=4)

        # Transactions table
        cols = ("Date", "Account", "Category", "Payee", "Amount", "Note", "Planned?")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Date", width=100)
        self.tree.column("Account", width=120)
        self.tree.column("Category", width=120)
        self.tree.column("Payee", width=140)
        self.tree.column("Amount", width=100, anchor="e")
        self.tree.column("Note", width=240)
        self.tree.column("Planned?", width=80, anchor="center")
        self.tree.tag_configure("planned", foreground="gray40", font=("Segoe UI", 10, "italic"))
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # Footer sum (computed locally from table rows)
        self.sum_label = ttk.Label(self, text="Sum: $0.00", anchor="e")
        self.sum_label.pack(fill="x", padx=8, pady=(0, 6))

        # Buttons
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=6, pady=4)
        ttk.Button(buttons, text="Add", command=self.add_transaction).pack(side="left")
        ttk.Button(buttons, text="Edit", command=self.edit_transaction).pack(side="left", padx=4)
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(side="left", padx=4)
        ttk.Button(buttons, text="Toggle Planned", command=self.toggle_planned).pack(side="left", padx=4)

    # helpers
    def _dollar_ok(self, text: str) -> bool:
        return bool(re.fullmatch(r"\$?\d+(\.\d{1,2})?", text.strip()))

    def _selected(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def refresh_sum(self):
        total = 0.0
        for i in self.tree.get_children():
            vals = self.tree.item(i, "values")
            try:
                total += float(vals[4])
            except Exception:
                pass
        self.sum_label.config(text=f"Sum: ${total:,.2f}")

    # Dialogs/actions
    def add_transaction(self):
        d = tk.Toplevel(self); d.title("Add Transaction"); d.geometry("320x340"); d.resizable(False, False)
        date_var = tk.StringVar(value=date.today().isoformat())
        account_var = tk.StringVar()
        category_var = tk.StringVar()
        payee_var = tk.StringVar()
        amount_var = tk.StringVar()
        note_var = tk.StringVar()
        planned_var = tk.StringVar(value="No")

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Date", make_date_triple(d, date_var))
        row(1, "Account", ttk.Entry(d, textvariable=account_var, width=20))
        row(2, "Category", ttk.Entry(d, textvariable=category_var, width=20))
        row(3, "Payee", ttk.Entry(d, textvariable=payee_var, width=20))
        row(4, "Amount ($)", ttk.Entry(d, textvariable=amount_var, width=12))
        row(5, "Note", ttk.Entry(d, textvariable=note_var, width=25))
        row(6, "Planned?", ttk.Combobox(d, textvariable=planned_var, values=["Yes", "No"], width=8, state="readonly"))

        def save():
            amt_text = amount_var.get().strip()
            if not self._dollar_ok(amt_text):
                messagebox.showerror("Invalid Amount", "Enter a valid dollar amount (e.g., 10 or 10.50)."); return

            planned = (planned_var.get() == "Yes")
            self.tree.insert("", "end",
                values=[
                    date_var.get(), account_var.get(), category_var.get(), payee_var.get(),
                    f"{float(amt_text.replace('$','')):.2f}", note_var.get(), "Yes" if planned else "No"
                ],
                tags=("planned",) if planned else ()
            )
            self.refresh_sum()
            d.destroy()

        ttk.Button(d, text="Save", command=save).grid(row=7, column=0, columnspan=2, pady=10)

    def edit_transaction(self):
        sel = self._selected()
        if not sel:
            messagebox.showinfo("Edit", "Select a transaction to edit."); return
        item_vals = self.tree.item(sel, "values")

        d = tk.Toplevel(self); d.title("Edit Transaction"); d.geometry("340x360"); d.resizable(False, False)
        date_var = tk.StringVar(value=item_vals[0])
        account_var = tk.StringVar(value=item_vals[1])
        category_var = tk.StringVar(value=item_vals[2])
        payee_var = tk.StringVar(value=item_vals[3])
        amount_var = tk.StringVar(value=str(item_vals[4]))
        note_var = tk.StringVar(value=item_vals[5])
        planned_var = tk.StringVar(value=item_vals[6])

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Date", make_date_triple(d, date_var))
        row(1, "Account", ttk.Entry(d, textvariable=account_var, width=22))
        row(2, "Category", ttk.Entry(d, textvariable=category_var, width=22))
        row(3, "Payee", ttk.Entry(d, textvariable=payee_var, width=22))
        row(4, "Amount ($)", ttk.Entry(d, textvariable=amount_var, width=12))
        row(5, "Note", ttk.Entry(d, textvariable=note_var, width=26))
        row(6, "Planned?", ttk.Combobox(d, textvariable=planned_var, values=["Yes", "No"], width=8, state="readonly"))

        def save():
            amt_text = amount_var.get().strip()
            if not self._dollar_ok(amt_text):
                messagebox.showerror("Invalid Amount", "Enter a valid dollar amount (e.g., 10 or 10.50)."); return
            planned = (planned_var.get() == "Yes")
            self.tree.item(sel,
                values=[
                    date_var.get(), account_var.get(), category_var.get(), payee_var.get(),
                    f"{float(amt_text.replace('$','')):.2f}", note_var.get(), "Yes" if planned else "No"
                ],
                tags=("planned",) if planned else ()
            )
            self.refresh_sum()
            d.destroy()

        ttk.Button(d, text="Save", command=save).grid(row=7, column=0, columnspan=2, pady=10)

    def delete_selected(self):
        selected = self._selected()
        if not selected: return
        self.tree.delete(selected)
        self.refresh_sum()

    def toggle_planned(self):
        if getattr(self, "_showing_planned_only", False):
            #this part is broken because there isn't an orm implementation yet.
            for i in self.tree.get_children():
                self.tree.reattach(i, '', 'end')
            self._showing_planned_only = False
        else:
            for i in self.tree.get_children():
                vals = self.tree.item(i, "values")
                if vals and vals[-1] != "Yes":
                    self.tree.detach(i)
            self._showing_planned_only = True

class BudgetsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._build_ui()

    def _build_ui(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=4)
        ttk.Label(bar, text="Month:").pack(side="left")
        months = [f"{i:02d}" for i in range(1, 13)]
        self.month_var = tk.StringVar(value=datetime.now().strftime("%m"))
        ttk.Combobox(bar, textvariable=self.month_var, values=months, width=4, state="readonly").pack(side="left", padx=2)
        years = [str(y) for y in range(datetime.now().year - 5, datetime.now().year + 6)]
        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        ttk.Combobox(bar, textvariable=self.year_var, values=years, width=6, state="readonly").pack(side="left", padx=2)
        ttk.Button(bar, text="Refresh", command=_noop_refresh).pack(side="left", padx=4)

        cols = ("Category", "Target", "Spent", "Remaining", "Status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # demo rows so you can see styling/behavior (temporary)
        self._load_demo()

        # inline edit for "Target" on double-click
        self.tree.bind("<Double-1>", self._edit_target_cell)

    def _load_demo(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        demo = [
            ("Groceries", "300.00", "250.00", "50.00", "OK"),
            ("Rent", "800.00", "820.00", "-20.00", "Over"),
        ]
        for row in demo:
            self.tree.insert("", "end", values=row)

    def _edit_target_cell(self, event):
        sel = self.tree.selection()
        if not sel: return
        col = self.tree.identify_column(event.x)
        if col != "#2":
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
                entry.destroy(); return
            vals = list(self.tree.item(item, "values"))
            target = float(val.replace("$", ""))
            spent = float(vals[2])
            remaining = target - spent
            vals[1] = f"{target:.2f}"
            vals[3] = f"{remaining:.2f}"
            vals[4] = "Over" if remaining < 0 else "OK"
            self.tree.item(item, values=vals)
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

if __name__ == "__main__":
    MainWindow().mainloop()
