#!/usr/bin/env python3
"""
Database initialization script for GlobeTrotter
Works with both SQLite (development) and PostgreSQL (production)
"""
from app import app, db
import os

def init_database():
    """Initialize database tables using Flask-SQLAlchemy"""
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables defined in models.py
        db.create_all()
        
        print("✓ Database tables created successfully!")
        print("Tables created:")
        print("  - user")
        print("  - trips")
        print("  - trip_destinations")
        print("  - wishlist_items")
        print("  - notifications")
        print("  - trip_expenses")
        
        # Verify database connection
        try:
            from models import User
            count = User.query.count()
            print(f"\n✓ Database connection verified! ({count} users found)")
        except Exception as e:
            print(f"\n⚠ Warning: Could not verify database: {e}")

if __name__ == "__main__":
    init_database()
