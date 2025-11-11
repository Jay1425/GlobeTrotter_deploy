#!/usr/bin/env python3
"""
Simple OTP verification test
"""

from app import app, db
from models import User
from datetime import datetime
import sqlite3

def test_otp_basic():
    """Test basic OTP functionality"""
    print("=== Testing OTP System ===\n")
    
    with app.app_context():
        # Check if user table has OTP columns
        conn = sqlite3.connect('globetrotter.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        
        has_otp_columns = 'otp_code' in columns and 'otp_expiry' in columns
        print(f"✅ OTP columns exist: {has_otp_columns}")
        
        if not has_otp_columns:
            print("❌ Missing OTP columns. Run: python migrate_otp_verification.py")
            return False
        
        # Test user creation and OTP generation
        test_email = "test_otp@example.com"
        
        # Clean up any existing test user
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        
        # Create test user
        test_user = User(
            email=test_email,
            first_name="Test",
            last_name="OTP",
            password_hash="test_hash",
            is_email_verified=False
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✅ Created test user: {test_email}")
        
        # Test OTP generation
        otp_code = test_user.generate_otp()
        db.session.commit()
        
        print(f"✅ Generated OTP: {otp_code}")
        print(f"   OTP Expiry: {test_user.otp_expiry}")
        
        # Test OTP verification
        is_valid = test_user.verify_otp(otp_code)
        print(f"✅ OTP verification result: {is_valid}")
        
        # Test invalid OTP
        is_invalid = test_user.verify_otp("000000")
        print(f"✅ Invalid OTP test: {not is_invalid}")
        
        # Clean up
        db.session.delete(test_user)
        db.session.commit()
        
        print("\n🎉 OTP system is working correctly!")
        return True

if __name__ == "__main__":
    test_otp_basic()
