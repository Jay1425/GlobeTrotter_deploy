from app import app, db, User
import os

with app.app_context():
    # Check if admin user already exists
    admin_user = User.query.filter_by(email='admin@12345').first()
    
    if admin_user:
        print('Admin user already exists!')
        print(f'Email: {admin_user.email}')
        print(f'Is Admin: {admin_user.is_admin}')
        print(f'Is Active: {admin_user.is_active}')
        print(f'Is Email Verified: {admin_user.is_email_verified}')
    else:
        # Create admin user
        admin_user = User(
            first_name='Admin',
            last_name='User',
            email='admin@12345',
            phone_number='1234567890',
            is_admin=True,
            is_active=True,
            is_email_verified=True
        )
        admin_user.set_password('12345')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print('Admin user created successfully!')
        print('Email: admin@12345')
        print('Password: 12345')
        print('Admin privileges: Yes')
