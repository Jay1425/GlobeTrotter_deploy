#!/usr/bin/env python3
"""
Migration script to add new fields to TripDestination table
"""

from app import app, db
from models import TripDestination

def migrate_trip_destination_fields():
    """Add new fields to TripDestination table"""
    with app.app_context():
        try:
            # Check if new columns exist by trying to query them
            try:
                db.session.execute("SELECT budget, date_range, notes FROM trip_destinations LIMIT 1")
                print("New columns already exist, skipping migration")
                return
            except Exception:
                pass  # Columns don't exist, proceed with migration
            
            # Add new columns
            migrations = [
                "ALTER TABLE trip_destinations ADD COLUMN budget REAL",
                "ALTER TABLE trip_destinations ADD COLUMN date_range VARCHAR(100)",
                "ALTER TABLE trip_destinations ADD COLUMN notes TEXT"
            ]
            
            for migration in migrations:
                try:
                    db.session.execute(migration)
                    print(f"Executed: {migration}")
                except Exception as e:
                    print(f"Column might already exist: {e}")
            
            db.session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_trip_destination_fields()
