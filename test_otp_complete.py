#!/usr/bin/env python3
"""
Complete OTP system test including email verification
"""

from app import app, db, send_otp_email
from models import User
from flask import url_for
import requests
import time

def test_complete_otp_flow():
    """Test the complete OTP verification flow"""
    print("=== Testing Complete OTP Flow ===\n")
    
    with app.app_context():
        # Test 1: Create a new user (simulating signup)
        test_email = "otp_test@example.com"
        
        # Clean up any existing test user
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        
        print("1. Creating test user...")
        test_user = User(
            email=test_email,
            first_name="OTP",
            last_name="Test",
            password_hash="test_hash",
            is_email_verified=False
        )
        
        db.session.add(test_user)
        db.session.commit()
        print(f"   ✅ User created: {test_email}")
        
        # Test 2: Generate OTP
        print("\n2. Generating OTP...")
        otp_code = test_user.generate_otp()
        db.session.commit()
        print(f"   ✅ OTP generated: {otp_code}")
        print(f"   ✅ OTP expiry: {test_user.otp_expiry}")
        
        # Test 3: Test email sending (this will show if email config works)
        print("\n3. Testing email sending...")
        try:
            email_sent = send_otp_email(test_user, otp_code)
            if email_sent:
                print("   ✅ Email sent successfully!")
            else:
                print("   ❌ Email sending failed")
        except Exception as e:
            print(f"   ❌ Email error: {e}")
        
        # Test 4: Test OTP verification
        print("\n4. Testing OTP verification...")
        
        # Valid OTP
        is_valid = test_user.verify_otp(otp_code)
        print(f"   ✅ Valid OTP test: {is_valid}")
        
        # Invalid OTP
        is_invalid = test_user.verify_otp("999999")
        print(f"   ✅ Invalid OTP rejection: {not is_invalid}")
        
        # Test 5: Test verification completion
        print("\n5. Testing verification completion...")
        if test_user.verify_otp(otp_code):
            test_user.is_email_verified = True
            test_user.clear_otp()
            db.session.commit()
            print("   ✅ User verified and OTP cleared")
        
        # Test 6: Check final state
        print("\n6. Checking final state...")
        print(f"   Email verified: {test_user.is_email_verified}")
        print(f"   OTP code cleared: {test_user.otp_code is None}")
        print(f"   OTP expiry cleared: {test_user.otp_expiry is None}")
        
        # Clean up
        db.session.delete(test_user)
        db.session.commit()
        print("\n   ✅ Test user cleaned up")
        
        print("\n🎉 Complete OTP flow test completed!")

def test_signup_flow():
    """Test the signup flow with OTP"""
    print("\n=== Testing Signup Flow ===\n")
    
    with app.test_client() as client:
        # Test signup page loads
        response = client.get('/signup')
        print(f"1. Signup page status: {response.status_code}")
        
        # Test signup with new user
        signup_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'signup_test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        response = client.post('/signup', data=signup_data, follow_redirects=False)
        print(f"2. Signup response status: {response.status_code}")
        print(f"3. Signup redirect location: {response.location if response.status_code == 302 else 'No redirect'}")
        
        # Check if user was created
        with app.app_context():
            user = User.query.filter_by(email='signup_test@example.com').first()
            if user:
                print(f"4. User created successfully")
                print(f"   Email verified: {user.is_email_verified}")
                print(f"   Has OTP: {user.otp_code is not None}")
                
                # Clean up
                db.session.delete(user)
                db.session.commit()
            else:
                print("4. ❌ User not created")

if __name__ == "__main__":
    test_complete_otp_flow()
    test_signup_flow()
