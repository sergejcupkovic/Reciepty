import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "receipty.db"

def get_connection():
    """Returns a database connection that fetches rows as dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the expenses and items tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with get_connection() as connection:
        cursor = connection.cursor()
        


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            invoice_number TEXT UNIQUE,
            invoice_date DATE,
            total_amount REAL,
            invoice_text TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            name TEXT,
            quantity REAL,
            price REAL,
            total_price REAL,
            FOREIGN KEY (invoice_number) REFERENCES expenses (invoice_number)
        )
        """)
        connection.commit()

def insert_expense(company_name, invoice_number, invoice_date, total_amount, items, invoice_text=""):
    """Inserts a new parsed receipt and its items into the database."""
    with get_connection() as connection:
        cursor = connection.cursor()
   
        cursor.execute("""
        INSERT INTO expenses (company_name, invoice_number, invoice_date, total_amount, invoice_text)
        VALUES (?, ?, ?, ?, ?)
        """, (company_name, invoice_number, invoice_date, total_amount, invoice_text))
        expense_id = cursor.lastrowid
        
        for item in items:
            cursor.execute("""
            INSERT INTO items (invoice_number, name, quantity, price, total_price)
            VALUES (?, ?, ?, ?, ?)
            """, (invoice_number, item.get('name'), item.get('quantity'), item.get('price'), item.get('total_price')))
            
        connection.commit()
        return expense_id

def get_all_expenses():
    """Retrieves all expenses, including their connected items."""
    with get_connection() as connection:
        cursor = connection.cursor()
        
  
        cursor.execute("SELECT * FROM expenses ORDER BY invoice_date DESC")
        expense_rows = cursor.fetchall()
        
        expenses = []
        for row in expense_rows:
            expense = dict(row)
            inv_number = expense['invoice_number']
            
       
            cursor.execute("SELECT name, quantity, price, total_price FROM items WHERE invoice_number = ?", (inv_number,))
            item_rows = cursor.fetchall()
            

            expense['items'] = [dict(item_row) for item_row in item_rows]
            expenses.append(expense)
            
        return expenses

def get_expense_by_id(expense_id):
    """Retrieves a single expense by ID, including its full text."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        expense = dict(row)
        inv_number = expense['invoice_number']
        
        cursor.execute("SELECT name, quantity, price, total_price FROM items WHERE invoice_number = ?", (inv_number,))
        expense['items'] = [dict(item_row) for item_row in cursor.fetchall()]
        
        return expense

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
