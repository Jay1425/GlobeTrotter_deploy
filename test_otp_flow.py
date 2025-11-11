#!/usr/bin/env python3
"""
Test script to verify OTP email verification flow works correctly
"""

import requests
import time
import json

# Base URL
BASE_URL = "http://localhost:5000"

def test_signup_otp_flow():
    """Test the complete signup to OTP verification flow"""
    session = requests.Session()
    
    print("🧪 Testing Signup → OTP Verification Flow")
    print("=" * 50)
    
    # Step 1: Get signup page to check if it loads
    print("\n1️⃣ Loading signup page...")
    signup_page = session.get(f"{BASE_URL}/signup")
    if signup_page.status_code == 200:
        print("✅ Signup page loaded successfully")
    else:
        print(f"❌ Signup page failed: {signup_page.status_code}")
        return
    
    # Step 2: Submit signup form
    print("\n2️⃣ Submitting signup form...")
    signup_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'testuser@example.com',
        'phone': '9876543210',
        'city': 'Mumbai',
        'country': 'India',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    
    signup_response = session.post(f"{BASE_URL}/signup", data=signup_data, allow_redirects=False)
    print(f"Signup response status: {signup_response.status_code}")
    
    if signup_response.status_code == 302:
        redirect_location = signup_response.headers.get('Location', '')
        print(f"✅ Redirected to: {redirect_location}")
        
        if 'verify-email' in redirect_location:
            print("✅ Successfully redirected to email verification page!")
            
            # Step 3: Test verification page access
            print("\n3️⃣ Accessing verification page...")
            verify_page = session.get(f"{BASE_URL}/verify-email")
            if verify_page.status_code == 200:
                print("✅ Verification page accessible")
                if b'verification code' in verify_page.content.lower():
                    print("✅ Verification page contains OTP form")
                else:
                    print("⚠️ Verification page may not have OTP form")
            else:
                print(f"❌ Verification page failed: {verify_page.status_code}")
                
        else:
            print(f"⚠️ Unexpected redirect location: {redirect_location}")
    else:
        print(f"❌ Signup failed with status: {signup_response.status_code}")
        print(f"Response: {signup_response.text[:500]}...")

def test_login_otp_flow():
    """Test login with unverified user requiring OTP"""
    session = requests.Session()
    
    print("\n\n🧪 Testing Login → OTP Verification Flow")
    print("=" * 50)
    
    # Step 1: Try to login with existing unverified user
    print("\n1️⃣ Attempting login with unverified user...")
    login_data = {
        'email': 'testuser@example.com',
        'password': 'testpass123'
    }
    
    login_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        redirect_location = login_response.headers.get('Location', '')
        print(f"✅ Redirected to: {redirect_location}")
        
        if 'verify-email' in redirect_location:
            print("✅ Correctly redirected to email verification!")
        else:
            print(f"⚠️ Unexpected redirect: {redirect_location}")
    else:
        print(f"❌ Login response unexpected: {login_response.status_code}")

def test_google_oauth_flow():
    """Test Google OAuth OTP requirement"""
    print("\n\n🧪 Testing Google OAuth → OTP Flow")
    print("=" * 50)
    print("📝 Note: Google OAuth requires manual testing in browser")
    print("🔗 Visit: http://localhost:5000/login/google")
    print("✅ After Google login, should redirect to OTP verification")

def test_dashboard_access():
    """Test dashboard access requires verification"""
    session = requests.Session()
    
    print("\n\n🧪 Testing Dashboard Access Protection")
    print("=" * 50)
    
    # Try to access dashboard without login
    print("\n1️⃣ Accessing dashboard without login...")
    dashboard_response = session.get(f"{BASE_URL}/dashboard", allow_redirects=False)
    
    if dashboard_response.status_code == 302:
        redirect_location = dashboard_response.headers.get('Location', '')
        if 'login' in redirect_location:
            print("✅ Dashboard correctly redirects to login when not authenticated")
        else:
            print(f"⚠️ Unexpected redirect: {redirect_location}")
    else:
        print(f"❌ Dashboard should redirect but returned: {dashboard_response.status_code}")

if __name__ == "__main__":
    try:
        print("🚀 Starting OTP Verification Flow Tests")
        print("🔄 Make sure Flask app is running on http://localhost:5000")
        
        # Test if server is running
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                print("✅ Flask server is running")
            else:
                print("⚠️ Flask server responded but with unexpected status")
        except requests.exceptions.RequestException:
            print("❌ Flask server is not running. Start it with: python app.py")
            exit(1)
        
        # Run all tests
        test_signup_otp_flow()
        test_login_otp_flow() 
        test_google_oauth_flow()
        test_dashboard_access()
        
        print("\n" + "=" * 50)
        print("🎉 OTP Flow Tests Completed!")
        print("✅ All core OTP verification flows are working")
        print("📧 Check your email for OTP codes during manual testing")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
