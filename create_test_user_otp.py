#!/usr/bin/env python3
"""
Manual OTP verification test
"""

from app import app, db, send_otp_email
from models import User
from werkzeug.security import generate_password_hash

def create_test_user_with_otp():
    """Create a test user and show OTP for manual verification"""
    print("=== Creating Test User for Manual OTP Verification ===\n")
    
    with app.app_context():
        test_email = "manual_test@example.com"
        
        # Clean up any existing test user
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
            print("✅ Cleaned up existing test user")
        
        # Create test user
        test_user = User(
            email=test_email,
            first_name="Manual",
            last_name="Test",
            password_hash=generate_password_hash("testpass123"),
            is_email_verified=False
        )
        
        db.session.add(test_user)
        db.session.commit()
        print(f"✅ Created test user: {test_email}")
        
        # Generate OTP
        otp_code = test_user.generate_otp()
        db.session.commit()
        
        print(f"\n🔐 OTP Code: {otp_code}")
        print(f"📧 Email: {test_email}")
        print(f"🔒 Password: testpass123")
        print(f"⏰ OTP Expires: {test_user.otp_expiry}")
        
        # Send email
        print(f"\n📤 Sending verification email...")
        try:
            email_sent = send_otp_email(test_user, otp_code)
            if email_sent:
                print("✅ Verification email sent successfully!")
                print(f"📧 Check the email for OTP: {otp_code}")
            else:
                print("❌ Failed to send verification email")
        except Exception as e:
            print(f"❌ Email error: {e}")
        
        print(f"\n🌐 To test manually:")
        print(f"1. Go to: http://localhost:5000/verify-email")
        print(f"2. Enter OTP: {otp_code}")
        print(f"3. Or login with email: {test_email} and password: testpass123")
        
        print(f"\n💡 User ID: {test_user.id}")
        print(f"💡 To clean up later, run: DELETE FROM user WHERE email = '{test_email}';")

if __name__ == "__main__":
    create_test_user_with_otp()
