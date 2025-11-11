#!/usr/bin/env python3
"""
Migration script to add admin fields to users table
"""

import sqlite3
from datetime import datetime

def migrate_admin_fields():
    conn = sqlite3.connect('globetrotter.db')
    cursor = conn.cursor()
    
    try:
        print("Adding admin fields to user table...")
        
        # Add is_admin column
        try:
            cursor.execute('ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL')
            print("✓ Added is_admin column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✓ is_admin column already exists")
            else:
                print(f"✗ Error adding is_admin column: {e}")
        
        # Add last_login column
        try:
            cursor.execute('ALTER TABLE user ADD COLUMN last_login DATETIME')
            print("✓ Added last_login column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✓ last_login column already exists")
            else:
                print(f"✗ Error adding last_login column: {e}")
        
        # Add is_active column
        try:
            cursor.execute('ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL')
            print("✓ Added is_active column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✓ is_active column already exists")
            else:
                print(f"✗ Error adding is_active column: {e}")
        
        # Add password_hash column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE user ADD COLUMN password_hash VARCHAR(255)')
            print("✓ Added password_hash column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✓ password_hash column already exists")
            else:
                print(f"✗ Error adding password_hash column: {e}")
        
        # Create indices for better performance
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_is_admin ON user(is_admin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_is_active ON user(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_last_login ON user(last_login)')
            print("✓ Created indices for admin fields")
        except sqlite3.OperationalError as e:
            print(f"✗ Error creating indices: {e}")
        
        # Set all existing users as active
        cursor.execute('UPDATE user SET is_active = 1 WHERE is_active IS NULL')
        print("✓ Set all existing users as active")
        
        # Commit changes
        conn.commit()
        print("✓ Migration completed successfully!")
        
        # Create a default admin user if none exists
        cursor.execute('SELECT COUNT(*) FROM user WHERE is_admin = 1')
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            print("\n📋 No admin users found. Creating default admin...")
            from werkzeug.security import generate_password_hash
            
            # Check if we have any users to promote
            cursor.execute('SELECT id, email FROM user LIMIT 1')
            first_user = cursor.fetchone()
            
            if first_user:
                # Promote first user to admin
                cursor.execute('UPDATE user SET is_admin = 1 WHERE id = ?', (first_user[0],))
                conn.commit()
                print(f"✓ Promoted user {first_user[1]} (ID: {first_user[0]}) to admin")
            else:
                print("⚠️  No users found. Please create a user account first, then run this script again.")
        else:
            print(f"✓ Found {admin_count} admin user(s)")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_admin_fields()
