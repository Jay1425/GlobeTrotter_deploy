#!/usr/bin/env python3
"""
Test login flow for unverified users
"""

from app import app
from flask import session

def test_unverified_user_login():
    """Test what happens when unverified user tries to login"""
    with app.test_client() as client:
        # Try to login with the test user we created
        login_data = {
            'email': 'manual_test@example.com',
            'password': 'testpass123'
        }
        
        print("Testing login for unverified user...")
        response = client.post('/login', data=login_data, follow_redirects=False)
        print(f"Login status: {response.status_code}")
        print(f"Redirect location: {response.location if response.status_code == 302 else 'No redirect'}")
        
        # Follow the redirect to see what happens
        if response.status_code == 302:
            response = client.get(response.location, follow_redirects=False)
            print(f"After redirect status: {response.status_code}")
            if response.status_code == 302:
                print(f"Second redirect location: {response.location}")

if __name__ == "__main__":
    test_unverified_user_login()
