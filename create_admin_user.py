#!/usr/bin/env python3
"""
Create Admin User Script
Creates an admin user with email admin@12345 and password 12345
"""

import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def create_admin_user():
    """Create admin user with specified credentials"""
    
    with app.app_context():
        try:
            # Check if admin user already exists
            existing_admin = User.query.filter_by(email='admin@12345').first()
            
            if existing_admin:
                print("Admin user already exists. Updating credentials...")
                # Update existing user
                existing_admin.password_hash = generate_password_hash('12345')
                existing_admin.is_admin = True
                existing_admin.is_email_verified = True
                existing_admin.is_active = True
                existing_admin.first_name = 'Admin'
                existing_admin.last_name = 'User'
            else:
                print("Creating new admin user...")
                # Create new admin user
                admin_user = User(
                    email='admin@12345',
                    password_hash=generate_password_hash('12345'),
                    first_name='Admin',
                    last_name='User',
                    is_admin=True,
                    is_email_verified=True,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(admin_user)
            
            # Commit changes
            db.session.commit()
            
            print("✅ Admin user created/updated successfully!")
            print("📧 Email: admin@12345")
            print("🔐 Password: 12345")
            print("🛡️ Admin privileges: Enabled")
            print("✉️ Email verified: Yes")
            print("🔄 Status: Active")
            
            # Also make sure any existing admin@globetrotter.com is updated
            old_admin = User.query.filter_by(email='admin@globetrotter.com').first()
            if old_admin:
                print("\n🔄 Also updating old admin account...")
                old_admin.is_admin = True
                old_admin.is_email_verified = True
                old_admin.is_active = True
                db.session.commit()
                print("✅ Old admin account updated!")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {str(e)}")
            db.session.rollback()
            return False
            
    return True

def verify_admin_user():
    """Verify the admin user was created correctly"""
    
    with app.app_context():
        try:
            admin_user = User.query.filter_by(email='admin@12345').first()
            
            if admin_user:
                print(f"\n✅ Admin user verification:")
                print(f"👤 Name: {admin_user.first_name} {admin_user.last_name}")
                print(f"📧 Email: {admin_user.email}")
                print(f"🛡️ Is Admin: {admin_user.is_admin}")
                print(f"✉️ Email Verified: {admin_user.is_email_verified}")
                print(f"🔄 Is Active: {admin_user.is_active}")
                print(f"🆔 User ID: {admin_user.id}")
                
                return True
            else:
                print("❌ Admin user not found!")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying admin user: {str(e)}")
            return False

if __name__ == '__main__':
    print("🚀 Creating Admin User for GlobeTrotter...")
    print("=" * 50)
    
    if create_admin_user():
        verify_admin_user()
        print("\n🎉 Admin user setup complete!")
        print("\n🔗 You can now login to admin panel at:")
        print("   http://localhost:5000/admin/login")
        print("\n📝 Use these credentials:")
        print("   Email: admin@12345")
        print("   Password: 12345")
    else:
        print("❌ Failed to create admin user!")
        sys.exit(1)
