#!/usr/bin/env python3
"""
Migration script to add OTP verification fields to the User table
"""

import sqlite3
from datetime import datetime

def migrate_otp_fields():
    """Add OTP verification fields to user table"""
    
    # Connect to database
    conn = sqlite3.connect('globetrotter.db')
    cursor = conn.cursor()
    
    try:
        print("Starting OTP verification migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add is_email_verified column if it doesn't exist
        if 'is_email_verified' not in columns:
            print("Adding is_email_verified column...")
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN is_email_verified BOOLEAN DEFAULT 0 NOT NULL
            """)
            print("✓ Added is_email_verified column")
        else:
            print("✓ is_email_verified column already exists")
        
        # Add otp_code column if it doesn't exist
        if 'otp_code' not in columns:
            print("Adding otp_code column...")
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN otp_code VARCHAR(6)
            """)
            print("✓ Added otp_code column")
        else:
            print("✓ otp_code column already exists")
        
        # Add otp_expiry column if it doesn't exist
        if 'otp_expiry' not in columns:
            print("Adding otp_expiry column...")
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN otp_expiry DATETIME
            """)
            print("✓ Added otp_expiry column")
        else:
            print("✓ otp_expiry column already exists")
        
        # For existing users, mark admin users as email verified
        print("Setting email verification status for existing users...")
        cursor.execute("""
            UPDATE user 
            SET is_email_verified = 1 
            WHERE is_admin = 1
        """)
        
        # Commit the changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(user)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        expected_columns = ['is_email_verified', 'otp_code', 'otp_expiry']
        missing_columns = [col for col in expected_columns if col not in columns_after]
        
        if missing_columns:
            raise Exception(f"Migration incomplete. Missing columns: {missing_columns}")
        
        print("\n=== Migration Summary ===")
        print("✅ OTP verification fields added successfully!")
        print("✅ Admin users marked as email verified")
        print("✅ Database schema updated")
        
        # Show current user stats
        cursor.execute("SELECT COUNT(*) FROM user")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user WHERE is_email_verified = 1")
        verified_users = cursor.fetchone()[0]
        
        print(f"📊 Total users: {total_users}")
        print(f"📊 Email verified users: {verified_users}")
        print(f"📊 Unverified users: {total_users - verified_users}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_otp_fields()
    print("\n🎉 OTP verification migration completed!")
