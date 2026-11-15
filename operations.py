"""Database operations for the schema in init_retailDB.py.

Uses retailDB.create_connection(); run from the directory containing your database.
All writes use transactions and parameterized SQL. No tables or demo data are created.
"""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import sqlite3
from retailDB import create_connection


@contextmanager
def connection():
    db = create_connection()
    if db is None:
        raise RuntimeError('Could not connect to retail_store.db.')
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        with db:
            yield db
    finally:
        db.close()


def read(sql, parameters=()):
    with connection() as db:
        return [dict(row) for row in db.execute(sql, parameters)]


def integer(value, label='Quantity', minimum=0):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number != number.to_integral_value() or number < minimum:
            raise ValueError
        return int(number)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{label} must be a whole number of {minimum} or greater.') from None


def money(value, label='Price'):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or number != number.quantize(Decimal('0.01')):
            raise ValueError
        return str(number)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{label} must be nonnegative with at most two decimal places.') from None


def required(value, label):
    value = str(value or '').strip()
    if not value:
        raise ValueError(f'{label} is required.')
    return value


def get_categories():
    return read('SELECT * FROM Category ORDER BY category_name')


def get_products():
    return read('''SELECT p.*, c.category_name, i.quantity_on_hand,i.reorder_level
        FROM Product p LEFT JOIN Category c USING(category_id)
        LEFT JOIN Inventory i USING(product_id) ORDER BY p.product_id''')


def get_product(product_id):
    return next((row for row in get_products() if row['product_id'] == product_id), None)


def get_dashboard():
    return read('''SELECT (SELECT COUNT(*) FROM Product) AS products,
        (SELECT COUNT(*) FROM Inventory WHERE quantity_on_hand>0 AND quantity_on_hand<=reorder_level) AS low_stock,
        (SELECT COUNT(*) FROM Inventory WHERE quantity_on_hand=0) AS out_of_stock,
        (SELECT COUNT(*) FROM Category) AS categories''')[0]


def get_low_stock():
    return read('''SELECT p.product_name,i.quantity_on_hand,i.reorder_level FROM Product p
        JOIN Inventory i USING(product_id) WHERE i.quantity_on_hand<=i.reorder_level
        ORDER BY i.quantity_on_hand''')


def save_product(name, barcode, category_id, price, reorder_level, product_id=None, initial_quantity=0):
    name = required(name, 'Product name')
    barcode = str(barcode or '').strip() or None
    price = money(price)
    reorder = integer(reorder_level, 'Reorder level')
    quantity = integer(initial_quantity, 'Initial quantity')
    with connection() as db:
        if product_id is None:
            cursor = db.execute('INSERT INTO Product(product_name,barcode,category_id,selling_price) VALUES (?,?,?,?)', (name,barcode,category_id,price))
            product_id = cursor.lastrowid
            db.execute('INSERT INTO Inventory VALUES (?,?,?)',(product_id,quantity,reorder))
        else:
            cursor = db.execute('UPDATE Product SET product_name=?,barcode=?,category_id=?,selling_price=? WHERE product_id=?',(name,barcode,category_id,price,product_id))
            if cursor.rowcount != 1:
                raise ValueError('Product no longer exists.')
            db.execute('INSERT INTO Inventory VALUES (?,0,?) ON CONFLICT(product_id) DO UPDATE SET reorder_level=excluded.reorder_level',(product_id,reorder))
    return product_id


def adjust_stock(product_id, change):
    # Signed changes are allowed, but the resulting quantity must stay nonnegative.
    try:
        number = Decimal(str(change))
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError
        change = int(number)
    except (InvalidOperation, ValueError):
        raise ValueError('Stock change must be a whole number.') from None
    with connection() as db:
        db.execute('INSERT OR IGNORE INTO Inventory(product_id) VALUES (?)',(product_id,))
        cursor = db.execute('UPDATE Inventory SET quantity_on_hand=quantity_on_hand+? WHERE product_id=? AND quantity_on_hand+?>=0',(change,product_id,change))
        if cursor.rowcount != 1:
            raise ValueError('This adjustment would make stock negative.')


def delete_product(product_id):
    with connection() as db:
        db.execute('DELETE FROM Inventory WHERE product_id=?',(product_id,))
        db.execute('DELETE FROM Product WHERE product_id=?',(product_id,))


# An allowlist keeps table and column identifiers out of user input.
ENTITIES = {
    'Categories': ('Category','category_id',('category_name',)),
    'Suppliers': ('Supplier','supplier_id',('supplier_name','phone','email')),
    'Employees': ('Employee','employee_id',('first_name','last_name','role','phone')),
}


def get_records(entity):
    table, pk, columns = ENTITIES[entity]
    return read(f'SELECT {pk},{",".join(columns)} FROM {table} ORDER BY {pk}')


def save_record(entity, values, record_id=None):
    table, pk, columns = ENTITIES[entity]
    data = [str(values.get(column) or '').strip() or None for column in columns]
    mandatory = {'Categories':('category_name',),'Suppliers':('supplier_name',),'Employees':('first_name','last_name','role')}[entity]
    for column in mandatory:
        required(values.get(column),column.replace('_',' ').title())
    with connection() as db:
        if entity == 'Categories':
            duplicate = db.execute('SELECT category_id FROM Category WHERE lower(trim(category_name))=lower(?) AND category_id!=?',(data[0],record_id or -1)).fetchone()
            if duplicate:
                raise ValueError('That category already exists.')
        if record_id is None:
            cursor = db.execute(f'INSERT INTO {table}({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',data)
            return cursor.lastrowid
        cursor = db.execute(f'UPDATE {table} SET {",".join(c+"=?" for c in columns)} WHERE {pk}=?',(*data,record_id))
        if cursor.rowcount != 1:
            raise ValueError('Record no longer exists.')
        return record_id


def delete_record(entity, record_id):
    table, pk, columns = ENTITIES[entity]
    with connection() as db:
        db.execute(f'DELETE FROM {table} WHERE {pk}=?',(record_id,))


def get_sales(product_id=None):
    sql = 'SELECT sale_id,sale_datetime,employee_id,payment_method,tax_amount FROM Sale'
    params = ()
    if product_id is not None:
        sql += ' WHERE sale_id IN (SELECT sale_id FROM SaleItem WHERE product_id=?)'
        params = (product_id,)
    return read(sql+' ORDER BY sale_id DESC',params)


def get_purchase_orders():
    return read('''SELECT p.purchase_order_id,s.supplier_name,p.order_date,p.status
        FROM PurchaseOrder p JOIN Supplier s USING(supplier_id) ORDER BY purchase_order_id DESC''')


def get_line_items(kind, record_id):
    if kind == 'Sales':
        return read('''SELECT si.line_number,p.product_name,si.quantity,si.unit_price,si.discount_amount
            FROM SaleItem si JOIN Product p USING(product_id) WHERE si.sale_id=? ORDER BY si.line_number''',(record_id,))
    if kind == 'Purchase Orders':
        return read('''SELECT p.product_id,p.product_name,i.quantity_ordered,i.quantity_received,i.unit_cost
            FROM PurchaseOrderItem i JOIN Product p USING(product_id) WHERE i.purchase_order_id=?''',(record_id,))
    raise ValueError('Unknown record type.')


def create_sale(employee_id, payment_method, items, tax_amount=0):
    """items: [{product_id, quantity}]. Prices come from Product, never the UI.

    Stock deductions and the entire receipt commit together or all roll back.
    Tax is supplied explicitly; this project does not infer tax jurisdiction rules.
    """
    if payment_method not in ('Cash','Card','Other'):
        raise ValueError('Choose Cash, Card, or Other.')
    if not items:
        raise ValueError('Add at least one sale item.')
    tax = money(tax_amount,'Tax')
    with connection() as db:
        sale_id = db.execute('INSERT INTO Sale(employee_id,payment_method,tax_amount) VALUES (?,?,?)',(employee_id,payment_method,tax)).lastrowid
        for line,item in enumerate(items,1):
            quantity = integer(item['quantity'],'Quantity',1)
            product_id = integer(item['product_id'],'Product ID',1)
            product = db.execute('SELECT selling_price FROM Product WHERE product_id=?',(product_id,)).fetchone()
            if product is None:
                raise ValueError(f'Product #{product_id} does not exist.')
            price = money(product['selling_price'])
            cursor = db.execute('UPDATE Inventory SET quantity_on_hand=quantity_on_hand-? WHERE product_id=? AND quantity_on_hand>=?',(quantity,product_id,quantity))
            if cursor.rowcount != 1:
                raise ValueError(f'Insufficient stock for product #{product_id}.')
            db.execute('INSERT INTO SaleItem VALUES (?,?,?,?,?,0)',(sale_id,line,product_id,quantity,price))
        return sale_id


def create_purchase_order(supplier_id, items):
    """items: [{product_id, quantity_ordered, unit_cost}]. One row per product."""
    if not items:
        raise ValueError('Add at least one purchase order item.')
    with connection() as db:
        order_id = db.execute("INSERT INTO PurchaseOrder(supplier_id,status) VALUES (?,'Pending')",(supplier_id,)).lastrowid
        for item in items:
            db.execute('INSERT INTO PurchaseOrderItem VALUES (?,?,?,0,?)',(order_id,integer(item['product_id'],'Product ID',1),integer(item['quantity_ordered'],'Quantity',1),money(item['unit_cost'],'Unit cost')))
        return order_id


def receive_purchase_order(order_id, quantities):
    """quantities: {product_id: additional quantity received}."""
    if not quantities:
        raise ValueError('Specify quantities to receive.')
    with connection() as db:
        order = db.execute('SELECT status FROM PurchaseOrder WHERE purchase_order_id=?',(order_id,)).fetchone()
        if not order or order['status'] not in ('Pending','Partially Received'):
            raise ValueError('Only pending or partially received orders can be received.')
        for product_id, value in quantities.items():
            quantity = integer(value,'Quantity received',1)
            cursor = db.execute('UPDATE PurchaseOrderItem SET quantity_received=quantity_received+? WHERE purchase_order_id=? AND product_id=? AND quantity_received+?<=quantity_ordered',(quantity,order_id,product_id,quantity))
            if cursor.rowcount != 1:
                raise ValueError('Product is not on this order, or quantity exceeds the remaining order.')
            db.execute('INSERT INTO Inventory(product_id,quantity_on_hand) VALUES (?,?) ON CONFLICT(product_id) DO UPDATE SET quantity_on_hand=quantity_on_hand+excluded.quantity_on_hand',(product_id,quantity))
        remaining = db.execute('SELECT COUNT(*) FROM PurchaseOrderItem WHERE purchase_order_id=? AND quantity_received<quantity_ordered',(order_id,)).fetchone()[0]
        db.execute('UPDATE PurchaseOrder SET status=? WHERE purchase_order_id=?',('Partially Received' if remaining else 'Received',order_id))


def cancel_purchase_order(order_id):
    with connection() as db:
        cursor = db.execute("UPDATE PurchaseOrder SET status='Cancelled' WHERE purchase_order_id=? AND status='Pending' AND NOT EXISTS (SELECT 1 FROM PurchaseOrderItem WHERE purchase_order_id=? AND quantity_received>0)",(order_id,order_id))
        if cursor.rowcount != 1:
            raise ValueError('Only an unreceived pending order can be cancelled.')
