import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.exc import IntegrityError
from db.models import Category, Transaction, Budget


class CategoriesTab(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self._item_ids = {}  # Map treeview item IDs to category IDs
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # Filter bar
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=4)

        ttk.Label(bar, text="Type:").pack(side="left")
        self.type_var = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self.type_var, values=[
                     "All", "Income", "Expense"], width=12, state="readonly").pack(side="left", padx=4)

        ttk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.apply_filters())
        ttk.Entry(bar, textvariable=self.search_var,
                  width=16).pack(side="left", padx=4)

        ttk.Button(bar, text="Apply", command=self.apply_filters).pack(
            side="left", padx=4)

        # Categories table
        cols = ("Name", "Type", "Description")
        self.tree = ttk.Treeview(
            self, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("Name", width=200)
        self.tree.column("Type", width=120)
        self.tree.column("Description", width=200)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # Buttons
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=6, pady=4)
        ttk.Button(buttons, text="Add",
                   command=self.add_category).pack(side="left")
        ttk.Button(buttons, text="Edit", command=self.edit_category).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(
            side="left", padx=4)
        ttk.Button(buttons, text="Refresh", command=self.load_data).pack(
            side="left", padx=4)

    def load_data(self):
        """Load categories from database."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._item_ids.clear()

        categories = self.session.query(Category).all()
        for cat in categories:
            item_id = self.tree.insert("", "end",
                                       values=[cat.name, cat.type, cat.description or ""])
            self._item_ids[item_id] = cat.id
        self.apply_filters()

    def apply_filters(self):
        """Apply filters to category list."""
        type_filter = self.type_var.get()
        search_filter = self.search_var.get().lower().strip()

        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            name = values[0].lower()
            desc = (values[2] or "").lower()
            cat_type = values[1]

            # Type filter
            if type_filter != "All" and cat_type != type_filter:
                self.tree.detach(item_id)
                continue

            # Search filter
            if search_filter and search_filter not in name and search_filter not in desc:
                self.tree.detach(item_id)
                continue

            # Show item
            if item_id not in self.tree.get_children():
                self.tree.reattach(item_id, "", "end")

    # helpers
    def _selected(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _get_category_id(self, item_id):
        """Get category ID from treeview item ID."""
        return self._item_ids.get(item_id)

    # Dialogs/actions
    def add_category(self):
        d = tk.Toplevel(self)
        d.title("Add Category")
        d.geometry("320x180")
        d.resizable(False, False)
        name_var = tk.StringVar()
        type_var = tk.StringVar(value="Expense")
        description_var = tk.StringVar()

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(
                row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Name", ttk.Entry(d, textvariable=name_var, width=20))
        row(1, "Type", ttk.Combobox(d, textvariable=type_var, values=[
            "Income", "Expense"], width=18, state="readonly"))
        row(2, "Description", ttk.Entry(d, textvariable=description_var, width=22))

        def save():
            if not name_var.get().strip():
                messagebox.showerror(
                    "Invalid Name", "Category name is required.")
                return

            try:
                category = Category(
                    name=name_var.get().strip(),
                    type=type_var.get(),
                    description=description_var.get().strip()
                )
                self.session.add(category)
                self.session.commit()
                self.load_data()
                self.main_window.refresh_all_tabs()
                d.destroy()
            except IntegrityError:
                self.session.rollback()
                messagebox.showerror(
                    "Error", "A category with this name already exists.")
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to save category: {str(e)}")

        button_frame = ttk.Frame(d)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save",
                   command=save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=d.destroy).pack(side="left", padx=5)

    def edit_category(self):
        sel = self._selected()
        if not sel:
            messagebox.showinfo("Edit", "Select a category to edit.")
            return

        cat_id = self._get_category_id(sel)
        if not cat_id:
            return

        category = self.session.query(Category).filter_by(id=cat_id).first()
        if not category:
            return

        item_vals = self.tree.item(sel, "values")

        d = tk.Toplevel(self)
        d.title("Edit Category")
        d.geometry("340x200")
        d.resizable(False, False)
        name_var = tk.StringVar(value=item_vals[0])
        type_var = tk.StringVar(value=item_vals[1])
        description_var = tk.StringVar(value=item_vals[2])

        def row(r, label, widget):
            ttk.Label(d, text=label).grid(
                row=r, column=0, sticky="e", padx=6, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=6, pady=4)

        row(0, "Name", ttk.Entry(d, textvariable=name_var, width=22))
        row(1, "Type", ttk.Combobox(d, textvariable=type_var, values=[
            "Income", "Expense"], width=20, state="readonly"))
        row(2, "Description", ttk.Entry(d, textvariable=description_var, width=26))

        def save():
            if not name_var.get().strip():
                messagebox.showerror(
                    "Invalid Name", "Category name is required.")
                return

            try:
                # Check if name changed and if new name conflicts
                if name_var.get().strip() != category.name:
                    existing = self.session.query(Category).filter_by(
                        name=name_var.get().strip()).first()
                    if existing:
                        messagebox.showerror(
                            "Error", "A category with this name already exists.")
                        return

                category.name = name_var.get().strip()
                category.type = type_var.get()
                category.description = description_var.get().strip()
                self.session.commit()
                self.load_data()
                self.main_window.refresh_all_tabs()
                d.destroy()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to update category: {str(e)}")

        button_frame = ttk.Frame(d)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save",
                   command=save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=d.destroy).pack(side="left", padx=5)

    def delete_selected(self):
        selected = self._selected()
        if not selected:
            messagebox.showinfo("Delete", "Select a category to delete.")
            return

        cat_id = self._get_category_id(selected)
        if not cat_id:
            return

        category = self.session.query(Category).filter_by(id=cat_id).first()
        if not category:
            return

        # Check if category is used by transactions or budgets
        transaction_count = self.session.query(Transaction).filter_by(
            category_id=cat_id).count()
        budget_count = self.session.query(Budget).filter_by(
            category_id=cat_id).count()

        if transaction_count > 0 or budget_count > 0:
            messagebox.showerror(
                "Cannot Delete",
                f"This category is used by {transaction_count} transaction(s) and {budget_count} budget(s). "
                "Please delete or update them first.")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete category '{category.name}'?"):
            try:
                self.session.delete(category)
                self.session.commit()
                self.load_data()
                self.main_window.refresh_all_tabs()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror(
                    "Error", f"Failed to delete category: {str(e)}")
