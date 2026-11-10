import sqlite3
from retailDB import create_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS Category (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Product (
    product_id INTEGER PRIMARY KEY,
    barcode TEXT UNIQUE,
    product_name TEXT NOT NULL,
    category_id INTEGER,
    selling_price NUMERIC NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);

CREATE TABLE IF NOT EXISTS Inventory (
    product_id INTEGER PRIMARY KEY,
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    reorder_level INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE IF NOT EXISTS Supplier (
    supplier_id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    phone TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS PurchaseOrder (
    purchase_order_id INTEGER PRIMARY KEY,
    supplier_id INTEGER NOT NULL,
    order_date TEXT NOT NULL DEFAULT CURRENT_DATE,
    status TEXT NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
);

CREATE TABLE IF NOT EXISTS PurchaseOrderItem (
    purchase_order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_ordered INTEGER NOT NULL,
    quantity_received INTEGER NOT NULL DEFAULT 0,
    unit_cost NUMERIC NOT NULL,
    PRIMARY KEY (purchase_order_id, product_id),
    FOREIGN KEY (purchase_order_id) REFERENCES PurchaseOrder(purchase_order_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE IF NOT EXISTS Employee (
    employee_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS Sale (
    sale_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    sale_datetime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tax_amount NUMERIC NOT NULL DEFAULT 0,
    payment_method TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
);

CREATE TABLE IF NOT EXISTS SaleItem (
    sale_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC NOT NULL,
    discount_amount NUMERIC NOT NULL DEFAULT 0,
    PRIMARY KEY (sale_id, line_number),
    FOREIGN KEY (sale_id) REFERENCES Sale(sale_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);
"""


def initialize_database(database_path="retail_store.db"):
    """Create the retail tables without removing existing tables or data.

    Dates use SQLite's ISO text format. Foreign key enforcement must also
    be enabled on each connection that subsequently writes to the database.
    """
    conn = create_connection()
    cursor = conn.cursor()

    cursor.executescript(SCHEMA)
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()
