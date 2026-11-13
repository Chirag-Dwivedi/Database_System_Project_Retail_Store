import sqlite3 as sql 
import pandas as pd

# Category

with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from category
        """
    )
    category = pd.DataFrame(cursor.fetchall())
# Product table

with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from product
        """
    )
    product = pd.DataFrame(cursor.fetchall(), columns=['product_id', 'barcode', 'product_name', 'category_id', 'selling_price'])


# Inventory table
with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from Inventory
        """
    )
    Inventory = pd.DataFrame(cursor.fetchall())


# Supplier table
with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from Supplier
        """
    )
    Supplier = pd.DataFrame(cursor.fetchall())


# PurchaseOrder table
with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from PurchaseOrder
        """
    )
    PurchaseOrder = pd.DataFrame(cursor.fetchall())


# PurchaseOrderItem table
with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from PurchaseOrderItem
        """
    )
    PurchaseOrderItem = pd.DataFrame(cursor.fetchall())


# Employee
with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from Employee
        """
    )
    Employee = pd.DataFrame(cursor.fetchall())


# Sale
with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * from Sale
        """
    )
    Sale = pd.DataFrame(cursor.fetchall())


# SaleItem
with sql.connect('retail_store.db') as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        select * 
        from SaleItem
        """
    )
    SaleItem = pd.DataFrame(cursor.fetchall())

product1 = (123,"fidgetspinner", 67, 43)
product2 = (1234,"fidgetcube", 67, 43)