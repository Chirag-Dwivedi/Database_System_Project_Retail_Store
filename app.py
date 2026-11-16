import matplotlib
import sqlite3 as sql 
import tkinter as tk 
import pandas as pd
from tkinter import messagebox

matplotlib.use('TkAgg')

conn = sql.connect('retail_store.db')
cursor = conn.cursor()

root = tk.Tk()

root.title('retailer_db')
root.geometry('500x500')

# --------- FUNCTIONS ---------

def add_category():
    cat_name = category_name.get().strip()
    
    if not cat_name:
        messagebox.showerror('e', 'real vals')
        return

    inputs = (cat_name)

    cursor.execute(
        """
        insert into Category (category_name)
        VALUES (?)
        """, inputs
    )
    conn.commit()

    load_categories()

def load_categories():
    listBox.delete(0, tk.END)

    cursor.execute(
        """
        select * from Category
        """        
        )
    categories = cursor.fetchall()

    for category in categories:
        listBox.insert(0, category)

def delete_category():
    selected = listBox.curselection()
    customer = listBox.get(selected[0])
    id = customer[0]

    cursor.execute(
        """
        delete from category
        where category_id = ?
        """, (id,)
    )
    conn.commit()

    load_categories()


# ---------TKinter variables--------

buttonadd = tk.Button(
    root,
    text='Add Category',
    command=add_category
)

buttonremove = tk.Button(
    root,
    text='Delete Category',
    command=delete_category
)


category_name = tk.Entry(root)

listBox = tk.Listbox(root, width=40)

# ---------HEADERS SENT-----------

load_categories()

category_name.pack()

buttonadd.pack()
buttonremove.pack()
listBox.pack()

root.mainloop()
cursor.close()
conn.close()