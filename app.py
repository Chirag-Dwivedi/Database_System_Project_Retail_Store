"""Tkinter UI for retailDB.py + operations.py. Run python init_retailDB.py first, then python app.py.
No SQL or connection code belongs in this UI module.
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import operations as ops

NAVY = '#111e32'
TEAL = '#008d86'
BG = '#f5f7fb'
INK = '#142035'
MUTED = '#657184'

class StoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Convenience Store Manager')
        self.geometry('1320x820')
        self.minsize(1040, 700)
        self.configure(bg=BG)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.report_callback_exception = self.callback_error
        self.page = 'Inventory'
        self.product_filter = None
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Treeview', font=('Segoe UI', 10), rowheight=42, background='white', fieldbackground='white', borderwidth=0)
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#edf1f6', foreground=INK, padding=10)
        style.map('Treeview', background=[('selected','#cdece8')], foreground=[('selected',INK)])
        style.configure('TCombobox', padding=7)
        self.sidebar = tk.Frame(self, bg=NAVY, width=230)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text='Convenience Store\nManager', font=('Segoe UI',18,'bold'), fg='white', bg=NAVY, justify='left').pack(anchor='w', padx=22, pady=(30,8))
        tk.Label(self.sidebar, text='Single-store management', fg='#b6c4d7', bg=NAVY, font=('Segoe UI',10)).pack(anchor='w', padx=22, pady=(0,28))
        self.nav = {}
        for name in ['Dashboard','Products','Categories','Inventory','Sales','Purchase Orders','Suppliers','Employees']:
            b = tk.Button(self.sidebar, text=name, anchor='w', command=lambda n=name: self.navigate(n), font=('Segoe UI',12), fg='white', bg=NAVY, activebackground=TEAL, activeforeground='white', bd=0, padx=18, pady=13, cursor='hand2')
            b.pack(fill='x', padx=10, pady=3)
            self.nav[name] = b
        tk.Label(self.sidebar, text='SQLite • Desktop application', bg=NAVY, fg='#b6c4d7', font=('Segoe UI',9)).pack(side='bottom', pady=20)
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side='left', fill='both', expand=True, padx=26, pady=24)
        self.navigate('Inventory')

    def callback_error(self, kind, error, traceback):
        messagebox.showerror('Action failed', str(error), parent=self)

    def close(self):
        self.destroy()

    def button(self, parent, text, command, primary=False):
        b = tk.Button(parent, text=text, command=command, bg=TEAL if primary else 'white', fg='white' if primary else TEAL, activebackground='#dcefeb', relief='flat', font=('Segoe UI',10,'bold'), padx=16, pady=10, cursor='hand2', highlightbackground='#ccd6df', highlightthickness=1)
        return b

    def label(self, parent, text, size=11, bold=False, color=INK, bg=BG):
        return tk.Label(parent, text=text, font=('Segoe UI',size,'bold' if bold else 'normal'), fg=color, bg=bg, anchor='w')

    def navigate(self, page, product_id=None):
        self.page, self.product_filter = page, product_id
        for name, b in self.nav.items():
            b.configure(bg=TEAL if name == page else NAVY)
        for child in self.main.winfo_children():
            child.destroy()
        header = tk.Frame(self.main, bg=BG)
        header.pack(fill='x')
        self.label(header, page, 28, True).pack(side='left')
        self.button(header, 'Refresh', lambda: self.navigate(self.page, self.product_filter)).pack(side='right')
        if page in ('Inventory','Products'):
            self.button(header, '+ Add Product', self.product_form, True).pack(side='right', padx=10)
        self.label(self.main, {'Inventory':'Track stock and reorder products', 'Products':'Manage your product catalog', 'Dashboard':'Your store at a glance'}.get(page, 'Manage your store records'), color=MUTED).pack(fill='x', pady=(4,20))
        if page in ('Inventory','Products','Dashboard'):
            self.cards()
        if page in ('Inventory','Products'):
            self.inventory_page()
        elif page == 'Dashboard':
            self.label(self.main, 'Products needing attention', 16, True).pack(anchor='w', pady=(20,10))
            rows = [tuple(row.values()) for row in ops.get_low_stock()]
            self.table(self.main, ['Product','In Stock','Reorder At'], rows)
            self.button(self.main, 'Open Inventory', lambda: self.navigate('Inventory'), True).pack(anchor='w', pady=15)
        else:
            self.records_page()
        self.label(self.main, 'Database: retail_store.db', 9, color=MUTED).pack(side='bottom', anchor='e', pady=(8,0))

    def cards(self):
        summary = ops.get_dashboard()
        counts = [summary[key] for key in ('products','low_stock','out_of_stock','categories')]
        frame = tk.Frame(self.main,bg=BG)
        frame.pack(fill='x', pady=(0,20))
        for i,(title,value,color) in enumerate(zip(['Products','Low Stock','Out of Stock','Categories'],counts,[TEAL,'#ad6800','#bd3333',TEAL])):
            frame.columnconfigure(i, weight=1, uniform='cards')
            card = tk.Frame(frame,bg='white',highlightbackground='#d9e0e8',highlightthickness=1)
            card.grid(row=0,column=i,sticky='ew',padx=(0,10 if i<3 else 0))
            self.label(card,title,10,True,bg='white').pack(anchor='w',padx=15,pady=(15,0))
            self.label(card,str(value),25,True,color,bg='white').pack(anchor='w',padx=15,pady=(2,15))

    def table(self, parent, columns, rows, height=10):
        box = tk.Frame(parent,bg='white')
        box.pack(fill='both',expand=True)
        tree = ttk.Treeview(box,columns=list(range(len(columns))),show='headings',height=height)
        for i,name in enumerate(columns):
            tree.heading(i,text=name)
            tree.column(i,width=130,minwidth=70,anchor='w')
        tree.pack(side='left',fill='both',expand=True)
        scroll = ttk.Scrollbar(box,orient='vertical',command=tree.yview)
        scroll.pack(side='right',fill='y')
        tree.configure(yscrollcommand=scroll.set)
        horizontal = ttk.Scrollbar(parent,orient='horizontal',command=tree.xview)
        horizontal.pack(fill='x')
        tree.configure(xscrollcommand=horizontal.set)
        for row in rows:
            tree.insert('', 'end', values=tuple('' if x is None else x for x in row))
        return tree

    def inventory_page(self):
        filters = tk.Frame(self.main,bg=BG)
        filters.pack(fill='x',pady=(0,14))
        self.search = tk.StringVar()
        self.category = tk.StringVar(value='All Categories')
        self.stock = tk.StringVar(value='All Stock Levels')
        self.categories = {str(r['category_id'])+' • '+r['category_name']:r['category_id'] for r in ops.get_categories()}
        entry = ttk.Entry(filters,textvariable=self.search,font=('Segoe UI',11))
        entry.pack(side='left',fill='x',expand=True,ipady=7)
        entry.bind('<Return>',lambda event:self.load_inventory())
        self.button(filters,'Search',self.load_inventory).pack(side='left',padx=6)
        for variable,values in [(self.category,['All Categories',*self.categories]),(self.stock,['All Stock Levels','In Stock','Low Stock','Out of Stock','Missing Inventory'])]:
            combo = ttk.Combobox(filters,textvariable=variable,values=values,state='readonly',width=20)
            combo.pack(side='left',padx=4)
            combo.bind('<<ComboboxSelected>>',lambda event:self.load_inventory())
        self.tree = self.table(self.main,['ID','Product Name','Category','Price','In Stock','Reorder At','Status'],[])
        self.tree.column(1,width=210)
        self.tree.column(0,width=70)
        self.tree.tag_configure('Low Stock',foreground='#996000')
        self.tree.tag_configure('Out of Stock',foreground='#ba3030')
        self.tree.bind('<<TreeviewSelect>>',self.select_product)
        self.tree.bind('<Double-1>',lambda event:self.edit_selected())
        panel = tk.Frame(self.main,bg='white',highlightbackground='#d9e0e8',highlightthickness=1)
        panel.pack(fill='x',pady=(20,4))
        self.selection_label = self.label(panel,'Select a product to manage its stock',14,True,bg='white')
        self.selection_label.pack(anchor='w',padx=16,pady=(16,8))
        actions = tk.Frame(panel,bg='white')
        actions.pack(fill='x',padx=16,pady=(0,16))
        for text,command in [('Adjust Stock',self.adjust_stock),('Edit Product',self.edit_selected),('View Sales',self.view_sales),('Delete Product',self.delete_product)]:
            self.button(actions,text,command, text=='Adjust Stock').pack(side='left',padx=(0,8))
        self.row_count = self.label(self.main,'',9,color=MUTED)
        self.row_count.pack(anchor='w')
        self.load_inventory()

    def load_inventory(self):
        selected = self.tree.selection()
        previous = selected[0] if selected else None
        self.tree.delete(*self.tree.get_children())
        rows = ops.get_products()
        for row in rows:
            quantity,level = row['quantity_on_hand'],row['reorder_level']
            status = 'Missing Inventory' if quantity is None else 'Out of Stock' if quantity==0 else 'Low Stock' if quantity<=level else 'In Stock'
            query = self.search.get().strip().casefold()
            if query and query not in f"{row['product_name']} {row['barcode'] or ''} {row['product_id']}".casefold():
                continue
            if self.category.get() in self.categories and row['category_id']!=self.categories[self.category.get()]:
                continue
            if self.stock.get() != 'All Stock Levels' and self.stock.get()!=status:
                continue
            self.tree.insert('','end',iid=str(row['product_id']),values=(row['product_id'],row['product_name'],row['category_name'] or 'Uncategorized',f"${row['selling_price']:.2f}",quantity if quantity is not None else '—',level if level is not None else '—',status),tags=(status,))
        children = self.tree.get_children()
        self.row_count.configure(text=f'{len(children)} products shown • Double-click a row to edit')
        if children:
            self.tree.selection_set(previous if previous in children else children[0])
        else:
            self.selection_label.configure(text='No matching products')

    def selected_id(self):
        rows = self.tree.selection()
        if not rows:
            messagebox.showinfo('Select a product','Choose a product row first.',parent=self)
            return None
        return int(rows[0])

    def select_product(self,event=None):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0],'values')
            self.selection_label.configure(text=f'Selected: {values[1]}    •    Stock: {values[4]}    •    Reorder at: {values[5]}')

    def edit_selected(self):
        product_id = self.selected_id()
        if product_id is not None:
            self.product_form(product_id)

    def product_form(self, product_id=None):
        row = ops.get_product(product_id) if product_id is not None else None
        choices = {f"{r['category_id']} • {r['category_name']}":r['category_id'] for r in ops.get_categories()}
        win = tk.Toplevel(self)
        win.title('Edit Product' if row else 'Add Product')
        win.geometry('450x530')
        win.resizable(False,False)
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()
        fields = {}
        specs = [('Product name',row['product_name'] if row else ''),('Barcode',row['barcode'] or '' if row else ''),('Selling price',str(row['selling_price']) if row else '0.00'),('Category',next((k for k,v in choices.items() if row and v==row['category_id']),next(iter(choices),''))),('Reorder level',str(row['reorder_level'] if row and row['reorder_level'] is not None else 5))]
        if not row:
            specs.append(('Initial quantity','0'))
        for label,value in specs:
            self.label(win,label,10,True).pack(anchor='w',padx=24,pady=(10,3))
            variable = tk.StringVar(value=value)
            fields[label] = variable
            widget = ttk.Combobox(win,textvariable=variable,values=list(choices),state='readonly') if label=='Category' else ttk.Entry(win,textvariable=variable)
            widget.pack(fill='x',padx=24,ipady=4)
            if label == 'Category':
                category_widget = widget
        def add_category():
            name = simpledialog.askstring('Create Category','Category name:',parent=win)
            if not name or not name.strip():
                return
            try:
                category_id = ops.save_record('Categories', {'category_name': name})
                key = f'{category_id} • {name.strip()}'
                choices[key] = category_id
                category_widget.configure(values=list(choices))
                fields['Category'].set(key)
            except (ValueError, sqlite3.Error) as error:
                messagebox.showerror('Cannot create category',str(error),parent=win)
        self.button(win,'+ Create Category',add_category,False).pack(anchor='w',padx=24,pady=10)
        def save():
            try:
                name = fields['Product name'].get().strip()
                if not name:
                    raise ValueError('Enter a product name.')
                category = choices.get(fields['Category'].get())
                if category is None:
                    raise ValueError('Choose a category. Create one first if none exist.')
                price = ops.money(fields['Selling price'].get())
                reorder = ops.integer(fields['Reorder level'].get(),'Reorder level')
                barcode = fields['Barcode'].get().strip() or None
                quantity = ops.integer(fields['Initial quantity'].get(),'Initial quantity') if not row else 0
                ops.save_product(name,barcode,category,price,reorder,product_id,quantity)
            except (ValueError,sqlite3.Error) as error:
                messagebox.showerror('Cannot save',str(error),parent=win)
                return
            win.destroy()
            self.navigate(self.page)
        self.button(win,'Save Product',save,True).pack(fill='x',padx=24,pady=10)

    def adjust_stock(self):
        product_id = self.selected_id()
        if product_id is None:
            return
        change = simpledialog.askinteger('Adjust Stock','Quantity change (e.g. 10 or -2):',parent=self)
        if change is None:
            return
        try:
            ops.adjust_stock(product_id,change)
        except (ValueError,sqlite3.Error) as error:
            messagebox.showerror('Cannot adjust stock',str(error),parent=self)
            return
        self.navigate(self.page)

    def delete_product(self):
        product_id = self.selected_id()
        if product_id is None or not messagebox.askyesno('Delete Product','Delete this product and its inventory row? Products referenced by sales or purchase orders cannot be deleted.',parent=self):
            return
        try:
            ops.delete_product(product_id)
        except sqlite3.IntegrityError:
            messagebox.showerror('Cannot delete','This product is referenced by a sale or purchase order. Its data has been retained.',parent=self)
            return
        self.navigate(self.page)

    def view_sales(self):
        product_id = self.selected_id()
        if product_id is not None:
            self.navigate('Sales',product_id)

    def records_page(self):
        entity = self.page
        if entity in ops.ENTITIES:
            table, pk, columns = ops.ENTITIES[entity]
            names = [pk, *columns]
            rows = ops.get_records(entity)
        elif entity == 'Sales':
            names = ['sale_id','sale_datetime','employee_id','payment_method','tax_amount']
            rows = ops.get_sales(self.product_filter)
        else:
            names = ['purchase_order_id','supplier_name','order_date','status']
            rows = ops.get_purchase_orders()
        if entity == 'Sales' and self.product_filter is not None:
            self.label(self.main,f'Filtered to product #{self.product_filter}',color=TEAL).pack(anchor='w')
        tree = self.table(self.main,[n.replace('_',' ').title() for n in names],[tuple(r[n] for n in names) for r in rows])
        self.label(self.main,f'{len(rows)} records',9,color=MUTED).pack(anchor='w',pady=8)
        actions = tk.Frame(self.main,bg=BG)
        actions.pack(fill='x',pady=10)
        def selected():
            ids = tree.selection()
            if not ids:
                messagebox.showinfo('Select a record','Choose a row first.',parent=self)
                return None
            return int(tree.item(ids[0],'values')[0])
        if entity in ops.ENTITIES:
            self.button(actions,'+ Add',lambda:self.record_form(entity),True).pack(side='left',padx=5)
            def edit():
                record_id = selected()
                if record_id is not None:
                    self.record_form(entity,next(r for r in rows if r[names[0]]==record_id))
            def delete():
                record_id = selected()
                if record_id is not None and messagebox.askyesno('Delete record','Delete the selected record? Referenced records cannot be deleted.',parent=self):
                    try:
                        ops.delete_record(entity,record_id)
                        self.navigate(entity)
                    except sqlite3.IntegrityError:
                        messagebox.showerror('Cannot delete','Other records reference this record.',parent=self)
            self.button(actions,'Edit',edit).pack(side='left',padx=5)
            self.button(actions,'Delete',delete).pack(side='left',padx=5)
            tree.bind('<Double-1>',lambda event:edit())
        else:
            tree.bind('<Double-1>',lambda event:self.show_line_items(tree))
            self.button(actions,'View Line Items',lambda:self.show_line_items(tree)).pack(side='left',padx=5)
            self.button(actions,'+ New Sale' if entity=='Sales' else '+ New Purchase Order',lambda:self.transaction_form(entity),True).pack(side='left',padx=5)
            if entity=='Purchase Orders':
                def cancel():
                    order_id = selected()
                    if order_id is not None and messagebox.askyesno('Cancel Order','Cancel this pending order?',parent=self):
                        ops.cancel_purchase_order(order_id)
                        self.navigate(entity)
                def receive():
                    order_id = selected()
                    if order_id is not None:
                        self.receive_form(order_id)
                self.button(actions,'Receive Stock',receive).pack(side='left',padx=5)
                self.button(actions,'Cancel Order',cancel).pack(side='left',padx=5)

    def record_form(self,entity,row=None):
        table,pk,columns = ops.ENTITIES[entity]
        win = tk.Toplevel(self)
        win.title(('Edit ' if row else 'Add ')+entity)
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()
        fields = {}
        for column in columns:
            self.label(win,column.replace('_',' ').title()).pack(anchor='w',padx=24,pady=(12,3))
            var = tk.StringVar(value=(row[column] or '') if row else '')
            fields[column] = var
            ttk.Entry(win,textvariable=var,width=40).pack(fill='x',padx=24,ipady=5)
        def save():
            try:
                ops.save_record(entity,{k:v.get() for k,v in fields.items()},row[pk] if row else None)
            except (ValueError,sqlite3.Error) as error:
                messagebox.showerror('Cannot save',str(error),parent=win)
                return
            win.destroy()
            self.navigate(entity)
        self.button(win,'Save',save,True).pack(fill='x',padx=24,pady=20)

    def transaction_form(self,entity):
        sale = entity=='Sales'
        people = ops.get_records('Employees' if sale else 'Suppliers')
        products = ops.get_products()
        if not people or not products:
            messagebox.showinfo('Missing records','Add products and an employee or supplier first.',parent=self)
            return
        win = tk.Toplevel(self)
        win.title('New Sale' if sale else 'New Purchase Order')
        win.geometry('850x650')
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()
        people_map = {f"{r['employee_id']} • {r['first_name']} {r['last_name']}":r['employee_id'] for r in people} if sale else {f"{r['supplier_id']} • {r['supplier_name']}":r['supplier_id'] for r in people}
        product_map = {f"{r['product_id']} • {r['product_name']}":r['product_id'] for r in products}
        def combo(label,choices):
            self.label(win,label).pack(anchor='w',padx=20,pady=(8,3))
            var = tk.StringVar(value=next(iter(choices)))
            ttk.Combobox(win,textvariable=var,values=list(choices),state='readonly').pack(fill='x',padx=20)
            return var
        person = combo('Employee' if sale else 'Supplier',people_map)
        payment = combo('Payment Method',['Cash','Card','Other']) if sale else None
        product = combo('Product',product_map)
        quantity = tk.StringVar(value='1')
        amount = tk.StringVar(value='0.00')
        self.label(win,'Quantity').pack(anchor='w',padx=20,pady=(8,3))
        ttk.Entry(win,textvariable=quantity).pack(fill='x',padx=20)
        if not sale:
            self.label(win,'Unit Cost').pack(anchor='w',padx=20,pady=(8,3))
            ttk.Entry(win,textvariable=amount).pack(fill='x',padx=20)
        items = []
        tree = None
        def add():
            try:
                pid = product_map[product.get()]
                qty = ops.integer(quantity.get(),'Quantity',1)
                if not sale and any(i['product_id']==pid for i in items):
                    raise ValueError('Each product may appear once per purchase order. Remove its row to change it.')
                cost = ops.money(amount.get(),'Unit cost') if not sale else next(r['selling_price'] for r in products if r['product_id']==pid)
                items.append({'product_id':pid,'quantity':qty,'quantity_ordered':qty,'unit_cost':cost})
                tree.insert('','end',values=(pid,product.get().split(' • ',1)[1],qty,cost))
            except (ValueError,KeyError) as error:
                messagebox.showerror('Invalid item',str(error),parent=win)
        self.button(win,'Add Item',add).pack(anchor='w',padx=20,pady=8)
        tree = self.table(win,['Product ID','Product','Quantity','Unit Price' if sale else 'Unit Cost'],[],height=4)
        def remove():
            ids = tree.selection()
            if ids:
                index = tree.index(ids[0])
                items.pop(index)
                tree.delete(ids[0])
        self.button(win,'Remove Selected Item',remove).pack(anchor='w',padx=20,pady=5)
        tax = tk.StringVar(value='0.00')
        if sale:
            self.label(win,'Tax amount (enter explicitly)').pack(anchor='w',padx=20)
            ttk.Entry(win,textvariable=tax).pack(fill='x',padx=20)
        def submit():
            try:
                if sale:
                    ops.create_sale(people_map[person.get()],payment.get(),items,tax.get())
                else:
                    ops.create_purchase_order(people_map[person.get()],items)
            except (ValueError,sqlite3.Error) as error:
                messagebox.showerror('Cannot save',str(error),parent=win)
                return
            win.destroy()
            self.navigate(entity)
        self.button(win,'Complete Sale' if sale else 'Create Order',submit,True).pack(fill='x',padx=20,pady=12)

    def receive_form(self,order_id):
        # Each entry records an additional quantity, so partial deliveries are supported.
        rows = ops.get_line_items('Purchase Orders',order_id)
        win = tk.Toplevel(self)
        win.title(f'Receive Order #{order_id}')
        win.geometry('650x440')
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()
        fields = []
        canvas = tk.Canvas(win,bg=BG,highlightthickness=0)
        scroll = ttk.Scrollbar(win,orient='vertical',command=canvas.yview)
        scroll.pack(side='right',fill='y')
        canvas.pack(fill='both',expand=True)
        canvas.configure(yscrollcommand=scroll.set)
        inner = tk.Frame(canvas,bg=BG)
        canvas.create_window((0,0),window=inner,anchor='nw')
        inner.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
        for row in rows:
            self.label(inner,f"#{row['product_id']} {row['product_name']} — Remaining: {row['quantity_ordered']-row['quantity_received']}").pack(anchor='w',padx=20,pady=(12,3))
            var = tk.StringVar(value='0')
            ttk.Entry(inner,textvariable=var).pack(fill='x',padx=20)
            fields.append((row['product_id'],var))
        def receive():
            try:
                quantities = {pid:ops.integer(var.get(),'Quantity received') for pid,var in fields}
                ops.receive_purchase_order(order_id,{pid:q for pid,q in quantities.items() if q>0})
            except (ValueError,sqlite3.Error) as error:
                messagebox.showerror('Cannot receive',str(error),parent=win)
                return
            win.destroy()
            self.navigate('Purchase Orders')
        self.button(win,'Receive Stock',receive,True).pack(fill='x',padx=20,pady=12)

    def show_line_items(self,tree):
        if not tree.selection():
            messagebox.showinfo('Select a record','Choose a row first.',parent=self)
            return
        record_id = tree.item(tree.selection()[0],'values')[0]
        rows = ops.get_line_items(self.page,record_id)
        names = ['line_number','product_name','quantity','unit_price','discount_amount'] if self.page=='Sales' else ['product_id','product_name','quantity_ordered','quantity_received','unit_cost']
        win = tk.Toplevel(self)
        win.title(f'{self.page} #{record_id} — Line Items')
        win.geometry('900x400')
        self.table(win,[n.replace('_',' ').title() for n in names],[tuple(r[n] for n in names) for r in rows])


def main():
    try:
        ops.get_dashboard()
    except (sqlite3.Error,RuntimeError) as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('Database not ready',f'{error}\n\nRun python init_retailDB.py from your project folder first.',parent=root)
        root.destroy()
        return
    StoreApp().mainloop()


if __name__ == '__main__':
    main()
