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
        
        columns = [col['name'] for col in cursor.execute("PRAGMA table_info(expenses)").fetchall()]
        if 'tags' not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN tags TEXT DEFAULT ''")
        if 'original_url' not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN original_url TEXT DEFAULT ''")
        if 'important' not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN important BOOLEAN DEFAULT 0")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            color TEXT
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

def insert_expense(company_name, invoice_number, invoice_date, total_amount, items, invoice_text="", tags="", original_url="", important=False):
    """Inserts a new parsed receipt and its items into the database."""
    with get_connection() as connection:
        cursor = connection.cursor()
   
        cursor.execute("""
        INSERT INTO expenses (company_name, invoice_number, invoice_date, total_amount, invoice_text, tags, original_url, important)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (company_name, invoice_number, invoice_date, total_amount, invoice_text, tags, original_url, important))
        expense_id = cursor.lastrowid
        
        for item in items:
            cursor.execute("""
            INSERT INTO items (invoice_number, name, quantity, price, total_price)
            VALUES (?, ?, ?, ?, ?)
            """, (invoice_number, item.get('name'), item.get('quantity'), item.get('price'), item.get('total_price')))
            
        connection.commit()
        return expense_id

def get_all_expenses(search_query=None):
    """Retrieves all expenses, including their connected items."""
    with get_connection() as connection:
        cursor = connection.cursor()
        
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
  
        if search_query:
            query_val = f"%{search_query}%"
            query += " AND (invoice_text LIKE ? OR company_name LIKE ? OR tags LIKE ?)"
            params.extend([query_val, query_val, query_val])
            
        query += " ORDER BY invoice_date DESC"
        cursor.execute(query, tuple(params))
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

def get_all_tags():
    """Retrieves all tags."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tags ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

def add_tag(name, color):
    """Adds a new tag."""
    with get_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (name, color))
            connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def update_expense(expense_id, important):
    """Updates an existing expense's important flag."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE expenses SET important = ? WHERE id = ?", (important, expense_id))
        connection.commit()

def toggle_tag(expense_id, tag_name):
    """Toggles a tag on a specific expense."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT tags FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        if not row:
            return
            
        current_tags_str = row['tags'] or ""
        tags = [t.strip() for t in current_tags_str.split(',') if t.strip()]
        
        if tag_name in tags:
            tags.remove(tag_name)
        else:
            tags.append(tag_name)
            
        new_tags_str = ",".join(tags)
        cursor.execute("UPDATE expenses SET tags = ? WHERE id = ?", (new_tags_str, expense_id))
        connection.commit()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
