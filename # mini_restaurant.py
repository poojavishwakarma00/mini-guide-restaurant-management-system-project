# mini_restaurant.py  -- minimal Restaurant Billing (Tkinter + sqlite)
import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
from datetime import datetime

DB = "mini_rest.db"
def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS menu(id INTEGER PRIMARY KEY, name TEXT, price REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, ts TEXT, total REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER, name TEXT, qty INTEGER, price REAL)")
        c.commit()
        cur = c.execute("SELECT COUNT(*) FROM menu")
        if cur.fetchone()[0]==0:
            c.executemany("INSERT INTO menu(name,price) VALUES(?,?)",
                          [("Margherita",150),("Veg Burger",120),("Fries",60)])

def get_menu(): 
    with sqlite3.connect(DB) as c:
        return c.execute("SELECT id,name,price FROM menu").fetchall() 

def save_order(items):
    ts = datetime.now().isoformat(timespec="seconds")
    total = sum(q*price for _,_,q,price in items) # for menu_id, name, quantity, price in items
    with sqlite3.connect(DB) as c:
        cur = c.execute("INSERT INTO orders(ts,total) VALUES(?,?)",(ts,total))
        oid = cur.lastrowid
        c.executemany("INSERT INTO order_items(order_id,name,qty,price) VALUES(?,?,?,?)",
                      [(oid,name,q,price) for _,name,q,price in items])
        c.commit()
    return oid, ts, total

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Restaurant")
        self.geometry("520x300")
        self.cart=[]
        self.menu=get_menu()
        
        # Left: menu
        lf = tk.Frame(self)
        lf.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        tk.Label(lf,text="Menu").pack()
        self.lb = tk.Listbox(lf)
        self.lb.pack(fill="both",expand=True)
        
        for _id,name,price in self.menu:
            self.lb.insert("end", f"{name} — ₹{price}")
            
        tk.Button(lf,text="Add →",command=self.add_item).pack(pady=6)
        
        # Right: cart
        rf = tk.Frame(self)
        rf.pack(side="right",fill="both",expand=True,padx=8,pady=8)
        tk.Label(rf,text="Cart").pack()
        self.cl = tk.Listbox(rf); self.cl.pack(fill="both",expand=True)
        self.total_lbl = tk.Label(rf,text="Total: ₹0.00",font=("Arial",11,"bold")); self.total_lbl.pack(pady=6)
        tk.Button(rf,text="Remove",command=self.remove_sel).pack(fill="x")
        tk.Button(rf,text="Checkout",command=self.checkout).pack(fill="x",pady=6)

    def add_item(self):
        sel=self.lb.curselection()
        if not sel: 
            return messagebox.showinfo("Select","Choose an item first")
        idx=sel[0]
        mid,name,price=self.menu[idx]
        try:
            q = int(simpledialog.askstring("Qty","Enter quantity:",initialvalue="1",parent=self))
            if q<=0: raise ValueError
        except:
            return messagebox.showerror("Invalid","Quantity must be a positive integer")
            
        # merge if exists
        for i,(m_id,nm,qty,pr) in enumerate(self.cart):
            if nm==name:
                self.cart[i]=(m_id,nm,qty+q,pr)
                break
        else:
            self.cart.append((mid,name,q,price))
        self.refresh_cart()

    def refresh_cart(self):
        self.cl.delete(0,"end")
        total=0
        for _,name,q,price in self.cart:
            self.cl.insert("end",f"{name} x{q} — ₹{q*price}")
            total += q*price
        self.total_lbl.config(text=f"Total: ₹{total:.2f}")

    def remove_sel(self):
        sel=self.cl.curselection()
        if not sel: 
            return
        self.cart.pop(sel[0])
        self.refresh_cart()

    def checkout(self):
        if not self.cart: return messagebox.showinfo("Empty","Cart is empty")
        if not messagebox.askyesno("Confirm","Place order?"): 
            return
        oid,ts,total = save_order(self.cart)
        receipt = f"Order #{oid}\nTime: {ts}\n\n" + "\n".join(f"{n} x{q} ₹{q*p}" for _,n,q,p in self.cart) + f"\n\nTotal: ₹{total:.2f}"
        self.cart=[]
        self.refresh_cart()
        messagebox.showinfo("Receipt", receipt)

if __name__=="__main__":
    init_db()
    App().mainloop()