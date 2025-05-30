import sqlite3
from tabulate import tabulate

def show_database():
    conn = sqlite3.connect('database/portfolio.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n=== Database Structure ===\n")
    
    for table in tables:
        table_name = table[0]
        print(f"\n--- {table_name} Table ---")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print("\nColumns:")
        print(tabulate(columns, headers=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'], tablefmt='grid'))
        
        # Get table contents
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        if rows:
            print("\nData:")
            headers = [col[1] for col in columns]
            print(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            print("\nNo data in table")
    
    conn.close()

if __name__ == "__main__":
    show_database() 