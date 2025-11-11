from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    # Check if admin user already exists
    existing_admin = User.query.filter_by(email='admin@12345').first()
    
    if existing_admin:
        print("Admin user already exists. Updating credentials...")
        existing_admin.password_hash = generate_password_hash('12345')
        existing_admin.is_admin = True
        existing_admin.is_email_verified = True
        existing_admin.is_active = True
        existing_admin.first_name = 'Admin'
        existing_admin.last_name = 'User'
    else:
        print("Creating new admin user...")
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
    
    db.session.commit()
    print("✅ Admin user created successfully!")
    print("📧 Email: admin@12345")
    print("🔐 Password: 12345")
