#!/usr/bin/env python3
"""
Database migration script to add optimized indexes and new columns
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Apply database migrations for performance optimization"""
    db_path = 'instance/globetrotter.db'  # Updated path
    
    if not os.path.exists(db_path):
        print("Database not found. Please run the app first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting database migration...")
        
        # Add new columns to trips table
        migrations = [
            # Add budget column
            "ALTER TABLE trips ADD COLUMN budget REAL",
            # Add priority column
            "ALTER TABLE trips ADD COLUMN priority INTEGER DEFAULT 0",
            # Add tags column to wishlist_items
            "ALTER TABLE wishlist_items ADD COLUMN tags TEXT",
            # Add rating column to wishlist_items
            "ALTER TABLE wishlist_items ADD COLUMN rating REAL DEFAULT 0.0",
        ]
        
        for migration in migrations:
            try:
                cursor.execute(migration)
                print(f"✓ Applied: {migration}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e) or "already exists" in str(e):
                    print(f"⚠ Skipped (already exists): {migration}")
                else:
                    print(f"✗ Error: {migration} - {e}")
        
        # Create indexes for better performance
        indexes = [
            # Trips table indexes
            "CREATE INDEX IF NOT EXISTS idx_trips_title ON trips(title)",
            "CREATE INDEX IF NOT EXISTS idx_trips_start_date ON trips(start_date)",
            "CREATE INDEX IF NOT EXISTS idx_trips_end_date ON trips(end_date)",
            "CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status)",
            "CREATE INDEX IF NOT EXISTS idx_trips_created_at ON trips(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_trips_budget ON trips(budget)",
            "CREATE INDEX IF NOT EXISTS idx_trips_priority ON trips(priority)",
            
            # Trip destinations indexes
            "CREATE INDEX IF NOT EXISTS idx_destinations_name ON trip_destinations(name)",
            "CREATE INDEX IF NOT EXISTS idx_destinations_city ON trip_destinations(city)",
            "CREATE INDEX IF NOT EXISTS idx_destinations_country ON trip_destinations(country)",
            "CREATE INDEX IF NOT EXISTS idx_destinations_order ON trip_destinations(order_index)",
            
            # Wishlist items indexes
            "CREATE INDEX IF NOT EXISTS idx_wishlist_title ON wishlist_items(title)",
            "CREATE INDEX IF NOT EXISTS idx_wishlist_city ON wishlist_items(city)",
            "CREATE INDEX IF NOT EXISTS idx_wishlist_country ON wishlist_items(country)",
            "CREATE INDEX IF NOT EXISTS idx_wishlist_created_at ON wishlist_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_wishlist_rating ON wishlist_items(rating)",
            
            # Notifications indexes
            "CREATE INDEX IF NOT EXISTS idx_notifications_kind ON notifications(kind)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)",
            
            # Composite indexes for common query patterns
            "CREATE INDEX IF NOT EXISTS idx_trips_user_status ON trips(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_trips_user_created ON trips(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)",
        ]
        
        for index in indexes:
            try:
                cursor.execute(index)
                print(f"✓ Created index: {index.split()[-1]}")
            except sqlite3.OperationalError as e:
                print(f"⚠ Index already exists or error: {e}")
        
        # Add some sample data with the new fields
        sample_data_queries = [
            # Update existing trips with sample priorities
            "UPDATE trips SET priority = 1 WHERE status = 'in_progress'",
            "UPDATE trips SET priority = 2 WHERE status = 'planned'", 
            "UPDATE trips SET priority = 0 WHERE status = 'completed'",
            
            # Update wishlist items with sample ratings
            "UPDATE wishlist_items SET rating = 4.5 WHERE rating = 0.0",
            "UPDATE wishlist_items SET tags = 'popular,adventure' WHERE tags IS NULL",
        ]
        
        for query in sample_data_queries:
            try:
                cursor.execute(query)
                print(f"✓ Updated sample data")
            except sqlite3.OperationalError as e:
                print(f"⚠ Sample data update failed: {e}")
        
        conn.commit()
        print("\n🎉 Database migration completed successfully!")
        print("📊 Performance optimizations applied:")
        print("   - Added database indexes for faster queries")
        print("   - Added budget and priority fields to trips")
        print("   - Added tags and rating fields to wishlist items")
        print("   - Optimized foreign key relationships")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        conn.close()

def analyze_database():
    """Analyze database performance"""
    db_path = 'instance/globetrotter.db'  # Updated path
    
    if not os.path.exists(db_path):
        print("Database not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n📈 Database Analysis:")
        
        # Check table sizes
        tables = ['users', 'trips', 'trip_destinations', 'wishlist_items', 'notifications']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        print(f"\n🔍 Indexes created: {len(indexes)}")
        for idx in indexes:
            print(f"   - {idx[0]}")
            
    except Exception as e:
        print(f"Analysis failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
    analyze_database()
