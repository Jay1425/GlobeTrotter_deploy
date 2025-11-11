#!/usr/bin/env python3
"""
Create database tables using Flask-SQLAlchemy
"""
import os
from datetime import date
from app import app
from models import db, User, Trip, TripDestination, WishlistItem, Notification

def create_tables():
    """Create all database tables"""
    with app.app_context():
        # Remove existing database file if it exists
        db_path = 'globetrotter.db'
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Print created tables
        print("\nCreated tables:")
        print("  - users")
        print("  - trips") 
        print("  - trip_destinations")
        print("  - wishlist_items")
        print("  - notifications")
        
        # Create some basic sample data
        create_sample_data()

def create_sample_data():
    """Create some sample data for testing"""
    try:
        # Create a sample user
        user = User(
            first_name="Jay",
            last_name="Chura", 
            email="jayraychura13@gmail.com",
            phone="1234567890",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            bio="Travel enthusiast and explorer"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        print(f"\nSample user created: {user.email}")
        
        # Create a sample trip
        trip = Trip(
            user_id=user.id,
            title="European Adventure",
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 15),
            status="planned",
            budget=50000.0
        )
        db.session.add(trip)
        db.session.commit()
        
        print(f"Sample trip created: {trip.title}")
        
        # Create trip destinations
        destinations = [
            TripDestination(
                trip_id=trip.id,
                name="Eiffel Tower",
                city="Paris",
                country="France",
                order_index=1,
                sequence=1
            ),
            TripDestination(
                trip_id=trip.id,
                name="Louvre Museum",
                city="Paris", 
                country="France",
                order_index=2,
                sequence=2
            )
        ]
        
        for dest in destinations:
            db.session.add(dest)
        
        db.session.commit()
        print(f"Sample destinations created: {len(destinations)} destinations")
        
        # Create a sample wishlist item
        wishlist = WishlistItem(
            user_id=user.id,
            title="Visit Santorini",
            city="Santorini",
            country="Greece",
            tags='["beach", "romantic", "sunset"]',
            rating=4.8
        )
        db.session.add(wishlist)
        db.session.commit()
        
        print(f"Sample wishlist item created: {wishlist.title}")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.session.rollback()

if __name__ == "__main__":
    create_tables()
