#!/usr/bin/env python3
"""
Test the verification flow by setting up the session properly
"""

from app import app
from flask import session

def test_verification_with_session():
    """Test verification with proper session setup"""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['verification_email'] = 'manual_test@example.com'
        
        # Now test the verification page
        response = client.get('/verify-email')
        print(f"Verification page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Verification page loads correctly")
            
            # Test OTP submission
            otp_data = {'otp_code': '331949'}  # Using the OTP from our test
            response = client.post('/verify-email', data=otp_data, follow_redirects=False)
            print(f"OTP submission status: {response.status_code}")
            print(f"Redirect location: {response.location if response.status_code == 302 else 'No redirect'}")
            
            if response.status_code == 302:
                print("✅ OTP verification successful - user redirected")
            else:
                print("❌ OTP verification failed")
        else:
            print("❌ Verification page failed to load")

if __name__ == "__main__":
    test_verification_with_session()
