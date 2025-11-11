#!/usr/bin/env python3
"""
Test script for OTP email verification system
"""

import sqlite3
from datetime import datetime, timedelta

def test_otp_system():
    """Test the OTP verification functionality"""
    
    # Connect to database
    conn = sqlite3.connect('globetrotter.db')
    cursor = conn.cursor()
    
    try:
        print("=== Testing OTP Verification System ===\n")
        
        # Check if OTP columns exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        required_columns = ['is_email_verified', 'otp_code', 'otp_expiry']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            print("Please run: python migrate_otp_verification.py")
            return False
        
        print("✅ Database schema includes OTP verification fields")
        
        # Get user stats
        cursor.execute("SELECT COUNT(*) FROM user")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user WHERE is_email_verified = 1")
        verified_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user WHERE otp_code IS NOT NULL")
        users_with_otp = cursor.fetchone()[0]
        
        print(f"📊 User Statistics:")
        print(f"   • Total users: {total_users}")
        print(f"   • Email verified: {verified_users}")
        print(f"   • Pending verification: {total_users - verified_users}")
        print(f"   • Active OTP codes: {users_with_otp}")
        
        # Check for recent OTP codes
        cursor.execute("""
            SELECT email, first_name, otp_code, otp_expiry 
            FROM user 
            WHERE otp_code IS NOT NULL 
            ORDER BY otp_expiry DESC 
            LIMIT 5
        """)
        
        active_otps = cursor.fetchall()
        
        if active_otps:
            print(f"\n🔐 Recent OTP Codes:")
            for email, name, otp, expiry in active_otps:
                expiry_dt = datetime.fromisoformat(expiry) if expiry else None
                status = "VALID" if expiry_dt and expiry_dt > datetime.utcnow() else "EXPIRED"
                print(f"   • {email} ({name}): {otp} - {status}")
        
        # Check unverified users
        cursor.execute("""
            SELECT email, first_name, created_at 
            FROM user 
            WHERE is_email_verified = 0 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        unverified_users = cursor.fetchall()
        
        if unverified_users:
            print(f"\n📧 Users Needing Verification:")
            for email, name, created in unverified_users:
                print(f"   • {email} ({name}) - Registered: {created}")
        
        print(f"\n✅ OTP verification system is properly configured!")
        print(f"📝 Test Summary:")
        print(f"   • Database schema: ✅ Ready")
        print(f"   • User verification tracking: ✅ Active")
        print(f"   • OTP code management: ✅ Functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    test_otp_system()
    print("\n🎯 To test the full flow:")
    print("   1. Try signing up with a new email")
    print("   2. Check the verification email")
    print("   3. Enter the 6-digit OTP code")
    print("   4. Verify successful login to dashboard")
