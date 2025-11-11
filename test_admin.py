import requests
import json

# Test admin login
login_data = {
    'email': 'admin@12345',
    'password': '12345'
}

print("🔍 Testing Admin Panel...")
print("=" * 40)

try:
    # Test login page access
    response = requests.get('http://localhost:5000/admin/login')
    print(f"✅ Admin login page accessible: {response.status_code == 200}")
    
    # Test admin login
    session = requests.Session()
    response = session.post('http://localhost:5000/admin/login', data=login_data)
    
    if response.status_code == 302:  # Redirect means successful login
        print("✅ Admin login successful!")
        
        # Test admin dashboard access
        dashboard_response = session.get('http://localhost:5000/admin')
        if dashboard_response.status_code == 200:
            print("✅ Admin dashboard accessible!")
        else:
            print(f"❌ Admin dashboard error: {dashboard_response.status_code}")
            
        # Test admin users page
        users_response = session.get('http://localhost:5000/admin/users')
        if users_response.status_code == 200:
            print("✅ Admin users page accessible!")
        else:
            print(f"❌ Admin users page error: {users_response.status_code}")
            
        # Test admin trips page
        trips_response = session.get('http://localhost:5000/admin/trips')
        if trips_response.status_code == 200:
            print("✅ Admin trips page accessible!")
        else:
            print(f"❌ Admin trips page error: {trips_response.status_code}")
            
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print("Response:", response.text[:200])
        
except Exception as e:
    print(f"❌ Error testing admin panel: {str(e)}")

print("\n🔗 Access admin panel at: http://localhost:5000/admin/login")
print("📧 Email: admin@12345")
print("🔐 Password: 12345")
