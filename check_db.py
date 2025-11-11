#!/usr/bin/env python3
import sqlite3

def check_database():
    conn = sqlite3.connect('globetrotter.db')
    cursor = conn.cursor()
    
    # Check if database exists and has tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    if tables:
        # Check each table structure
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                print(f"\nStructure of {table_name}:")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''} {'NOT NULL' if col[3] else ''}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
