"""Simple store-management app. Database functions are in operations.py."""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import operations as ops


PAGES = ["Dashboard", "Products", "Categories", "Inventory",
         "Sales", "Purchase Orders", "Suppliers", "Employees"]


class StoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Convenience Store Manager")
        self.geometry("1100x700")
        self.page = "Inventory"
        self.product_filter = None

        # Navigation
        sidebar = tk.Frame(self)
        sidebar.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(sidebar, text="Store Manager",
                 font=("Arial", 18, "bold")).pack(pady=10)

        for page in PAGES:
            tk.Button(sidebar, text=page, width=18,
                      command=lambda p=page: self.open_page(p)).pack(fill="x")

        self.content = tk.Frame(self)
        self.content.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        self.open_page("Inventory")

    # ---------- Common helpers ----------

    def clear_page(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command)

    def table(self, parent, columns, rows, height=12):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            height=height)
        for column in columns:
            tree.heading(column, text=column.replace("_", " ").title())
            tree.column(column, width=130)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        for row in rows:
            tree.insert("", "end", values=row)

        return tree

    def show_error(self, title, error, parent=None):
        messagebox.showerror(title, str(error), parent=parent or self)

    def open_page(self, page, product_id=None):
        self.page = page
        self.product_filter = product_id
        self.clear_page()

        header = tk.Frame(self.content)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text=page, font=("Arial", 22, "bold")).pack(side="left")
        self.button(header, "Refresh",
                    lambda: self.open_page(self.page, self.product_filter)
                    ).pack(side="right")

        if page in ("Products", "Inventory"):
            self.button(header, "Add Product", self.product_form).pack(side="right")

        if page == "Dashboard":
            self.show_dashboard()
        elif page in ("Products", "Inventory"):
            self.show_inventory()
        else:
            self.show_records()

    # ---------- Dashboard ----------

    def show_dashboard(self):
        summary = ops.get_dashboard()

        for key in ("products", "low_stock", "out_of_stock", "categories"):
            text = f"{key.replace('_', ' ').title()}: {summary[key]}"
            tk.Label(self.content, text=text, font=("Arial", 13)).pack(anchor="w")

        tk.Label(self.content, text="Products needing attention",
                 font=("Arial", 15, "bold")).pack(anchor="w", pady=(20, 5))

        rows = [(r["product_name"], r["quantity_on_hand"], r["reorder_level"])
                for r in ops.get_low_stock()]
        self.table(self.content, ["Product", "In Stock", "Reorder At"], rows)

    # ---------- Products and inventory ----------

    def show_inventory(self):
        filters = tk.Frame(self.content)
        filters.pack(fill="x", pady=5)

        self.search = tk.StringVar()
        self.category = tk.StringVar(value="All Categories")
        self.stock = tk.StringVar(value="All Stock Levels")

        self.categories = {
            f'{r["category_id"]} - {r["category_name"]}': r["category_id"]
            for r in ops.get_categories()
        }

        search_box = ttk.Entry(filters, textvariable=self.search)
        search_box.pack(side="left", fill="x", expand=True)
        search_box.bind("<Return>", lambda event: self.load_inventory())
        self.button(filters, "Search", self.load_inventory).pack(side="left")

        category_box = ttk.Combobox(
            filters, textvariable=self.category,
            values=["All Categories", *self.categories], state="readonly"
        )
        category_box.pack(side="left", padx=5)
        category_box.bind("<<ComboboxSelected>>",
                          lambda event: self.load_inventory())

        stock_options = ["All Stock Levels", "In Stock", "Low Stock",
                         "Out of Stock", "Missing Inventory"]
        stock_box = ttk.Combobox(filters, textvariable=self.stock,
                                 values=stock_options, state="readonly")
        stock_box.pack(side="left")
        stock_box.bind("<<ComboboxSelected>>",
                       lambda event: self.load_inventory())

        columns = (
            ["ID", "Barcode", "Product Name", "Category", "Selling Price"]
            if self.page == "Products" else
            ["ID", "Product Name", "Category", "Price",
             "In Stock", "Reorder At", "Status"]
        )
        self.products_table = self.table(self.content, columns, [])
        self.products_table.bind("<<TreeviewSelect>>", self.show_selection)
        self.products_table.bind("<Double-1>",
                                 lambda event: self.edit_product())

        self.selection_text = tk.StringVar(value="Select a product")
        tk.Label(self.content, textvariable=self.selection_text).pack(anchor="w",
                                                                     pady=8)

        actions = tk.Frame(self.content)
        actions.pack(fill="x")
        for text, action in [
            ("Adjust Stock", self.adjust_stock),
            ("Edit", self.edit_product),
            ("View Sales", self.view_sales),
            ("Delete", self.delete_product),
        ]:
            self.button(actions, text, action).pack(side="left", padx=3)

        self.count_text = tk.StringVar()
        tk.Label(self.content, textvariable=self.count_text).pack(anchor="w")
        self.load_inventory()

    def load_inventory(self):
        tree = self.products_table
        tree.delete(*tree.get_children())

        for r in ops.get_products():
            qty = r["quantity_on_hand"]
            reorder = r["reorder_level"]

            if qty is None:
                status = "Missing Inventory"
            elif qty == 0:
                status = "Out of Stock"
            elif qty <= reorder:
                status = "Low Stock"
            else:
                status = "In Stock"

            search_text = f'{r["product_name"]} {r["barcode"] or ""} {r["product_id"]}'
            if self.search.get().lower() not in search_text.lower():
                continue

            category_id = self.categories.get(self.category.get())
            if category_id and r["category_id"] != category_id:
                continue
            if self.stock.get() not in ("All Stock Levels", status):
                continue

            if self.page == "Products":
                values = (
                    r["product_id"], r["barcode"] or "-", r["product_name"],
                    r["category_name"] or "Uncategorized",
                    f'${r["selling_price"]:.2f}'
                )
            else:
                values = (
                    r["product_id"], r["product_name"],
                    r["category_name"] or "Uncategorized",
                    f'${r["selling_price"]:.2f}',
                    qty if qty is not None else "-",
                    reorder if reorder is not None else "-", status
                )
            tree.insert("", "end", iid=str(r["product_id"]), values=values)

        self.count_text.set(f"{len(tree.get_children())} products shown")

    def selected_product(self):
        selected = self.products_table.selection()
        if not selected:
            messagebox.showinfo("Select Product", "Select a product first.")
            return None
        return int(selected[0])

    def show_selection(self, event=None):
        selected = self.products_table.selection()
        if selected:
            values = self.products_table.item(selected[0], "values")
            if self.page == "Products":
                self.selection_text.set(f"Selected: {values[2]}")
            else:
                self.selection_text.set(
                    f"Selected: {values[1]} | Stock: {values[4]} | "
                    f"Reorder at: {values[5]}"
                )

    def edit_product(self):
        product_id = self.selected_product()
        if product_id is not None:
            self.product_form(product_id)

    def product_form(self, product_id=None):
        row = ops.get_product(product_id) if product_id else None
        categories = {
            f'{r["category_id"]} - {r["category_name"]}': r["category_id"]
            for r in ops.get_categories()
        }

        window = tk.Toplevel(self)
        window.title("Edit Product" if row else "Add Product")
        window.geometry("400x470")
        window.transient(self)
        window.grab_set()

        fields = {}
        defaults = {
            "Product name": row["product_name"] if row else "",
            "Barcode": (row["barcode"] or "") if row else "",
            "Selling price": str(row["selling_price"]) if row else "0.00",
            "Category": next(
                (name for name, cid in categories.items()
                 if row and cid == row["category_id"]),
                next(iter(categories), "")
            ),
            "Reorder level": str(
                row["reorder_level"] if row and
                row["reorder_level"] is not None else 5
            ),
        }
        if row is None:
            defaults["Initial quantity"] = "0"

        for name, default in defaults.items():
            tk.Label(window, text=name).pack(anchor="w", padx=15, pady=(8, 2))
            value = tk.StringVar(value=default)
            fields[name] = value

            if name == "Category":
                category_box = ttk.Combobox(
                    window, textvariable=value, values=list(categories),
                    state="readonly"
                )
                category_box.pack(fill="x", padx=15)
            else:
                ttk.Entry(window, textvariable=value).pack(fill="x", padx=15)

        def add_category():
            name = simpledialog.askstring("New Category", "Category name:",
                                          parent=window)
            if not name or not name.strip():
                return
            try:
                category_id = ops.save_record(
                    "Categories", {"category_name": name.strip()}
                )
                key = f"{category_id} - {name.strip()}"
                categories[key] = category_id
                category_box["values"] = list(categories)
                fields["Category"].set(key)
            except (ValueError, sqlite3.Error) as error:
                self.show_error("Cannot Add Category", error, window)

        self.button(window, "Add Category", add_category).pack(pady=8)

        def save():
            try:
                name = fields["Product name"].get().strip()
                category_id = categories.get(fields["Category"].get())
                if not name:
                    raise ValueError("Enter a product name.")
                if category_id is None:
                    raise ValueError("Choose a category.")

                initial_qty = (
                    ops.integer(fields["Initial quantity"].get(),
                                "Initial quantity")
                    if row is None else 0
                )

                ops.save_product(
                    name,
                    fields["Barcode"].get().strip() or None,
                    category_id,
                    ops.money(fields["Selling price"].get()),
                    ops.integer(fields["Reorder level"].get(), "Reorder level"),
                    product_id,
                    initial_qty
                )
            except (ValueError, sqlite3.Error) as error:
                self.show_error("Cannot Save Product", error, window)
                return

            window.destroy()
            self.open_page(self.page)

        self.button(window, "Save", save).pack(fill="x", padx=15, pady=12)

    def adjust_stock(self):
        product_id = self.selected_product()
        if product_id is None:
            return

        change = simpledialog.askinteger(
            "Adjust Stock", "Quantity change (example: 10 or -2):",
            parent=self
        )
        if change is None:
            return

        try:
            ops.adjust_stock(product_id, change)
            self.open_page(self.page)
        except (ValueError, sqlite3.Error) as error:
            self.show_error("Cannot Adjust Stock", error)

    def delete_product(self):
        product_id = self.selected_product()
        if product_id is None:
            return
        if not messagebox.askyesno("Delete Product", "Delete this product?"):
            return

        try:
            ops.delete_product(product_id)
            self.open_page(self.page)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Cannot Delete",
                "This product is used by a sale or purchase order."
            )

    def view_sales(self):
        product_id = self.selected_product()
        if product_id is not None:
            self.open_page("Sales", product_id)

    # ---------- Categories, suppliers, employees, sales, orders ----------

    def show_records(self):
        entity = self.page

        if entity in ops.ENTITIES:
            _, primary_key, columns = ops.ENTITIES[entity]
            names = [primary_key, *columns]
            records = ops.get_records(entity)
        elif entity == "Sales":
            names = ["sale_id", "sale_datetime", "employee_id",
                     "payment_method", "tax_amount"]
            records = ops.get_sales(self.product_filter)
        else:
            names = ["purchase_order_id", "supplier_name", "order_date", "status"]
            records = ops.get_purchase_orders()

        rows = [tuple(record[name] for name in names) for record in records]
        tree = self.table(self.content, names, rows)

        actions = tk.Frame(self.content)
        actions.pack(fill="x", pady=10)

        if entity in ops.ENTITIES:
            self.button(actions, "Add",
                        lambda: self.record_form(entity)).pack(side="left", padx=3)
            self.button(actions, "Edit",
                        lambda: self.edit_record(entity, tree, records,
                                                 primary_key)).pack(side="left", padx=3)
            self.button(actions, "Delete",
                        lambda: self.delete_record(entity, tree)).pack(side="left", padx=3)
            tree.bind("<Double-1>", lambda event: self.edit_record(
                entity, tree, records, primary_key
            ))
        else:
            self.button(actions, "View Items",
                        lambda: self.show_line_items(tree)).pack(side="left", padx=3)
            self.button(
                actions, "New Sale" if entity == "Sales" else "New Purchase Order",
                lambda: self.transaction_form(entity)
            ).pack(side="left", padx=3)

            if entity == "Purchase Orders":
                self.button(actions, "Receive Stock",
                            lambda: self.receive_selected(tree)).pack(side="left", padx=3)
                self.button(actions, "Cancel Order",
                            lambda: self.cancel_order(tree)).pack(side="left", padx=3)

    def selected_record_id(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Select a row first.")
            return None
        return int(tree.item(selected[0], "values")[0])

    def edit_record(self, entity, tree, records, primary_key):
        record_id = self.selected_record_id(tree)
        if record_id is None:
            return
        row = next(record for record in records
                   if record[primary_key] == record_id)
        self.record_form(entity, row)

    def delete_record(self, entity, tree):
        record_id = self.selected_record_id(tree)
        if record_id is None:
            return
        if not messagebox.askyesno("Delete Record", "Delete this record?"):
            return
        try:
            ops.delete_record(entity, record_id)
            self.open_page(entity)
        except sqlite3.IntegrityError:
            messagebox.showerror("Cannot Delete",
                                 "Another record uses this record.")

    def record_form(self, entity, row=None):
        _, primary_key, columns = ops.ENTITIES[entity]
        window = tk.Toplevel(self)
        window.title(("Edit " if row else "Add ") + entity)
        window.transient(self)
        window.grab_set()

        fields = {}
        for column in columns:
            label = column.replace("_", " ").title()
            tk.Label(window, text=label).pack(anchor="w", padx=15, pady=(8, 2))
            value = tk.StringVar(value=(row[column] or "") if row else "")
            fields[column] = value
            ttk.Entry(window, textvariable=value).pack(fill="x", padx=15)

        def save():
            try:
                data = {key: value.get() for key, value in fields.items()}
                ops.save_record(entity, data, row[primary_key] if row else None)
            except (ValueError, sqlite3.Error) as error:
                self.show_error("Cannot Save", error, window)
                return
            window.destroy()
            self.open_page(entity)

        self.button(window, "Save", save).pack(fill="x", padx=15, pady=12)

    # ---------- Sales and purchase orders ----------

    def transaction_form(self, entity):
        is_sale = entity == "Sales"
        people = ops.get_records("Employees" if is_sale else "Suppliers")
        products = ops.get_products()

        if not people or not products:
            messagebox.showinfo(
                "Missing Records",
                "Add products and an employee or supplier first."
            )
            return

        window = tk.Toplevel(self)
        window.title("New Sale" if is_sale else "New Purchase Order")
        window.geometry("650x600")
        window.transient(self)
        window.grab_set()

        if is_sale:
            people_choices = {
                f'{p["employee_id"]} - {p["first_name"]} {p["last_name"]}':
                p["employee_id"] for p in people
            }
        else:
            people_choices = {
                f'{p["supplier_id"]} - {p["supplier_name"]}': p["supplier_id"]
                for p in people
            }

        product_choices = {
            f'{p["product_id"]} - {p["product_name"]}': p["product_id"]
            for p in products
        }

        def dropdown(label, choices):
            tk.Label(window, text=label).pack(anchor="w", padx=15, pady=(8, 2))
            value = tk.StringVar(value=list(choices)[0])
            ttk.Combobox(window, textvariable=value, values=list(choices),
                         state="readonly").pack(fill="x", padx=15)
            return value

        person = dropdown("Employee" if is_sale else "Supplier", people_choices)
        payment = dropdown("Payment Method", ["Cash", "Card", "Other"]) if is_sale else None
        product = dropdown("Product", product_choices)

        quantity = tk.StringVar(value="1")
        tk.Label(window, text="Quantity").pack(anchor="w", padx=15, pady=(8, 2))
        ttk.Entry(window, textvariable=quantity).pack(fill="x", padx=15)

        cost = tk.StringVar(value="0.00")
        if not is_sale:
            tk.Label(window, text="Unit Cost").pack(anchor="w", padx=15, pady=(8, 2))
            ttk.Entry(window, textvariable=cost).pack(fill="x", padx=15)

        items = []
        item_table = self.table(
            window, ["Product ID", "Product", "Quantity", "Price/Cost"], [],
            height=5
        )

        def add_item():
            try:
                product_id = product_choices[product.get()]
                qty = ops.integer(quantity.get(), "Quantity", 1)

                if not is_sale and any(i["product_id"] == product_id for i in items):
                    raise ValueError("This product is already in the order.")

                price = (
                    next(p["selling_price"] for p in products
                         if p["product_id"] == product_id)
                    if is_sale else ops.money(cost.get(), "Unit Cost")
                )

                items.append({
                    "product_id": product_id,
                    "quantity": qty,
                    "quantity_ordered": qty,
                    "unit_cost": price
                })
                item_table.insert("", "end", values=(
                    product_id, product.get(), qty, price
                ))
            except (ValueError, KeyError) as error:
                self.show_error("Invalid Item", error, window)

        self.button(window, "Add Item", add_item).pack(pady=6)

        def remove_item():
            selected = item_table.selection()
            if selected:
                items.pop(item_table.index(selected[0]))
                item_table.delete(selected[0])

        self.button(window, "Remove Selected Item", remove_item).pack()

        tax = tk.StringVar(value="0.00")
        if is_sale:
            tk.Label(window, text="Tax Amount").pack(anchor="w", padx=15, pady=(8, 2))
            ttk.Entry(window, textvariable=tax).pack(fill="x", padx=15)

        def submit():
            try:
                if not items:
                    raise ValueError("Add at least one item.")

                if is_sale:
                    ops.create_sale(people_choices[person.get()],
                                    payment.get(), items, tax.get())
                else:
                    ops.create_purchase_order(people_choices[person.get()], items)
            except (ValueError, sqlite3.Error) as error:
                self.show_error("Cannot Save", error, window)
                return

            window.destroy()
            self.open_page(entity)

        self.button(window, "Complete" if is_sale else "Create Order",
                    submit).pack(fill="x", padx=15, pady=12)

    def receive_selected(self, tree):
        order_id = self.selected_record_id(tree)
        if order_id is not None:
            self.receive_form(order_id)

    def cancel_order(self, tree):
        order_id = self.selected_record_id(tree)
        if order_id is None:
            return
        if not messagebox.askyesno("Cancel Order", "Cancel this order?"):
            return
        try:
            ops.cancel_purchase_order(order_id)
            self.open_page("Purchase Orders")
        except (ValueError, sqlite3.Error) as error:
            self.show_error("Cannot Cancel Order", error)

    def receive_form(self, order_id):
        rows = ops.get_line_items("Purchase Orders", order_id)
        window = tk.Toplevel(self)
        window.title(f"Receive Order #{order_id}")
        window.geometry("500x450")
        window.transient(self)
        window.grab_set()

        fields = []
        for row in rows:
            remaining = row["quantity_ordered"] - row["quantity_received"]
            tk.Label(
                window, text=f'{row["product_name"]} - Remaining: {remaining}'
            ).pack(anchor="w", padx=15, pady=(8, 2))

            value = tk.StringVar(value="0")
            ttk.Entry(window, textvariable=value).pack(fill="x", padx=15)
            fields.append((row["product_id"], value))

        def receive():
            try:
                quantities = {}
                for product_id, value in fields:
                    qty = ops.integer(value.get(), "Quantity received")
                    if qty > 0:
                        quantities[product_id] = qty
                ops.receive_purchase_order(order_id, quantities)
            except (ValueError, sqlite3.Error) as error:
                self.show_error("Cannot Receive Stock", error, window)
                return

            window.destroy()
            self.open_page("Purchase Orders")

        self.button(window, "Receive Stock", receive).pack(fill="x", padx=15, pady=12)

    def show_line_items(self, tree):
        record_id = self.selected_record_id(tree)
        if record_id is None:
            return

        rows = ops.get_line_items(self.page, record_id)
        if self.page == "Sales":
            columns = ["line_number", "product_name", "quantity",
                       "unit_price", "discount_amount"]
        else:
            columns = ["product_id", "product_name", "quantity_ordered",
                       "quantity_received", "unit_cost"]

        window = tk.Toplevel(self)
        window.title(f"{self.page} #{record_id} - Items")
        window.geometry("800x350")
        self.table(window, columns,
                   [tuple(row[column] for column in columns) for row in rows])


def main():
    try:
        ops.get_dashboard()
    except (sqlite3.Error, RuntimeError) as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database Not Ready",
            f"{error}\n\nRun python init_retailDB.py first.",
            parent=root
        )
        root.destroy()
        return

    StoreApp().mainloop()


if __name__ == "__main__":
    main()
