#!/usr/bin/env python3
"""
Database migration script to add TripExpense table
Run this script to add the new expense tracking functionality to the database
"""

import sqlite3
import os
from datetime import datetime

# Database file path
DB_PATH = 'globetrotter.db'

def migrate_database():
    """Add TripExpense table to the database"""
    
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found!")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if trip_expenses table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='trip_expenses'
        """)
        
        if cursor.fetchone():
            print("TripExpense table already exists!")
            conn.close()
            return True
        
        # Create trip_expenses table
        cursor.execute("""
            CREATE TABLE trip_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                category VARCHAR(50) NOT NULL,
                amount REAL NOT NULL,
                description VARCHAR(500),
                expense_date DATE NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                destination_id INTEGER,
                FOREIGN KEY (trip_id) REFERENCES trips (id),
                FOREIGN KEY (destination_id) REFERENCES trip_destinations (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_trip_expenses_trip_id ON trip_expenses(trip_id)")
        cursor.execute("CREATE INDEX idx_trip_expenses_category ON trip_expenses(category)")
        cursor.execute("CREATE INDEX idx_trip_expenses_date ON trip_expenses(expense_date)")
        cursor.execute("CREATE INDEX idx_trip_expenses_destination_id ON trip_expenses(destination_id)")
        
        # Insert some sample expense data
        sample_expenses = [
            (1, 'accommodation', 3500.00, 'Hotel booking - 2 nights', '2024-01-15', None),
            (1, 'meals', 800.00, 'Dinner at local restaurant', '2024-01-15', 1),
            (1, 'transport', 1200.00, 'Flight tickets', '2024-01-14', None),
            (1, 'activities', 500.00, 'City tour', '2024-01-16', 1),
            (1, 'shopping', 300.00, 'Souvenirs', '2024-01-16', 1),
            (2, 'accommodation', 4200.00, 'Resort stay - 3 nights', '2024-02-10', None),
            (2, 'meals', 1500.00, 'Beach-side dining', '2024-02-11', 2),
            (2, 'transport', 2000.00, 'Train tickets', '2024-02-09', None),
            (2, 'activities', 1800.00, 'Water sports package', '2024-02-12', 2),
        ]
        
        cursor.executemany("""
            INSERT INTO trip_expenses (trip_id, category, amount, description, expense_date, destination_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_expenses)
        
        conn.commit()
        
        print("✅ Successfully created trip_expenses table with sample data!")
        print(f"Added {len(sample_expenses)} sample expense records")
        
        # Verify the table was created
        cursor.execute("SELECT COUNT(*) FROM trip_expenses")
        count = cursor.fetchone()[0]
        print(f"Total expenses in database: {count}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting TripExpense table migration...")
    if migrate_database():
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
