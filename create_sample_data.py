#!/usr/bin/env python3
"""
Create sample admin user and test data for the admin dashboard
"""

import sqlite3
import random
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash

def create_sample_data():
    conn = sqlite3.connect('globetrotter.db')
    cursor = conn.cursor()
    
    try:
        print("Creating sample admin user and test data...")
        
        # Create admin user
        admin_email = "admin@globetrotter.com"
        admin_password = generate_password_hash("admin123")
        
        cursor.execute('''
            INSERT OR REPLACE INTO user 
            (email, first_name, last_name, phone, city, country, date_of_birth, bio, 
             profile_picture, created_at, updated_at, is_admin, is_active, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            admin_email, "Admin", "User", "+1234567890", "New York", "USA", 
            "1990-01-01", "Administrator of GlobeTrotter", None,
            datetime.utcnow(), datetime.utcnow(), 1, 1, admin_password
        ))
        
        print(f"✓ Created admin user: {admin_email} (password: admin123)")
        
        # Create sample regular users
        sample_users = [
            ("john.doe@example.com", "John", "Doe", "+1234567891", "Los Angeles", "USA"),
            ("jane.smith@example.com", "Jane", "Smith", "+1234567892", "London", "UK"),
            ("raj.patel@example.com", "Raj", "Patel", "+1234567893", "Mumbai", "India"),
            ("emma.wilson@example.com", "Emma", "Wilson", "+1234567894", "Sydney", "Australia"),
            ("carlos.garcia@example.com", "Carlos", "Garcia", "+1234567895", "Madrid", "Spain"),
            ("sarah.johnson@example.com", "Sarah", "Johnson", "+1234567896", "Toronto", "Canada"),
            ("david.kim@example.com", "David", "Kim", "+1234567897", "Seoul", "South Korea"),
            ("lisa.brown@example.com", "Lisa", "Brown", "+1234567898", "Berlin", "Germany")
        ]
        
        user_ids = []
        for i, (email, first_name, last_name, phone, city, country) in enumerate(sample_users):
            password_hash = generate_password_hash("password123")
            created_date = datetime.utcnow() - timedelta(days=random.randint(1, 180))
            last_login = created_date + timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO user 
                (email, first_name, last_name, phone, city, country, date_of_birth, bio,
                 profile_picture, created_at, updated_at, is_admin, is_active, password_hash, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email, first_name, last_name, phone, city, country,
                date(1985 + i, random.randint(1, 12), random.randint(1, 28)),
                f"Travel enthusiast from {city}",
                None, created_date, created_date, 0, 1, password_hash, last_login
            ))
            
            user_ids.append(cursor.lastrowid)
        
        print(f"✓ Created {len(sample_users)} sample users")
        
        # Create sample trips
        sample_trips = [
            ("European Adventure", "Exploring the historic cities of Europe", 50000, 30),
            ("Asia Explorer", "Discovering the culture and cuisine of Asia", 75000, 45),
            ("American Road Trip", "Cross-country adventure across America", 60000, 21),
            ("African Safari", "Wildlife adventure in the African savanna", 120000, 14),
            ("Australian Outback", "Exploring the rugged Australian wilderness", 80000, 18),
            ("South American Journey", "Adventure through South America", 90000, 35),
            ("Nordic Adventure", "Northern lights and fjords tour", 70000, 25),
            ("Mediterranean Cruise", "Island hopping in the Mediterranean", 85000, 12),
            ("Japanese Cultural Tour", "Traditional Japan experience", 65000, 16),
            ("New Zealand Adventure", "Nature and adventure in New Zealand", 95000, 28)
        ]
        
        trip_ids = []
        for i, (name, description, budget, duration) in enumerate(sample_trips):
            user_id = user_ids[i % len(user_ids)]
            created_date = datetime.utcnow() - timedelta(days=random.randint(1, 120))
            start_date = created_date + timedelta(days=random.randint(10, 60))
            end_date = start_date + timedelta(days=duration)
            
            cursor.execute('''
                INSERT INTO trip 
                (user_id, name, description, start_date, end_date, budget, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, name, description, start_date.date(), end_date.date(), 
                budget, created_date, created_date
            ))
            
            trip_ids.append(cursor.lastrowid)
        
        print(f"✓ Created {len(sample_trips)} sample trips")
        
        # Create sample destinations
        destinations_data = [
            ("Paris", "France", "Europe"),
            ("Rome", "Italy", "Europe"),
            ("Tokyo", "Japan", "Asia"),
            ("Bangkok", "Thailand", "Asia"),
            ("New York", "USA", "North America"),
            ("Los Angeles", "USA", "North America"),
            ("Cairo", "Egypt", "Africa"),
            ("Cape Town", "South Africa", "Africa"),
            ("Sydney", "Australia", "Oceania"),
            ("Melbourne", "Australia", "Oceania"),
            ("Rio de Janeiro", "Brazil", "South America"),
            ("Buenos Aires", "Argentina", "South America"),
            ("Stockholm", "Sweden", "Europe"),
            ("Barcelona", "Spain", "Europe"),
            ("Kyoto", "Japan", "Asia"),
            ("Auckland", "New Zealand", "Oceania")
        ]
        
        dest_count = 0
        for trip_id in trip_ids:
            num_destinations = random.randint(2, 4)
            selected_destinations = random.sample(destinations_data, num_destinations)
            
            for city, country, continent in selected_destinations:
                arrival_date = date.today() + timedelta(days=random.randint(10, 60))
                departure_date = arrival_date + timedelta(days=random.randint(2, 7))
                
                cursor.execute('''
                    INSERT INTO trip_destination 
                    (trip_id, destination, arrival_date, departure_date, accommodation, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trip_id, f"{city}, {country}", arrival_date, departure_date,
                    f"Hotel in {city}", f"Exploring the beautiful city of {city}",
                    datetime.utcnow()
                ))
                
                dest_count += 1
        
        print(f"✓ Created {dest_count} sample destinations")
        
        # Create sample expenses
        expense_categories = ["accommodation", "meals", "transport", "activities", "shopping", "other"]
        expense_count = 0
        
        for trip_id in trip_ids:
            num_expenses = random.randint(5, 15)
            
            for _ in range(num_expenses):
                category = random.choice(expense_categories)
                amount = random.randint(500, 5000)
                expense_date = date.today() - timedelta(days=random.randint(1, 60))
                description = f"{category.title()} expense for trip"
                
                cursor.execute('''
                    INSERT INTO trip_expenses 
                    (trip_id, category, amount, description, expense_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    trip_id, category, amount, description, expense_date, datetime.utcnow()
                ))
                
                expense_count += 1
        
        print(f"✓ Created {expense_count} sample expenses")
        
        # Create sample notifications
        notification_messages = [
            ("Your trip to Paris is starting soon!", "trip_reminder"),
            ("Budget alert: You've spent 80% of your budget", "budget_alert"),
            ("New destination added to your wishlist", "wishlist_update"),
            ("Travel tips for your upcoming trip", "travel_tips"),
            ("Weather update for your destination", "weather_update")
        ]
        
        for user_id in user_ids:
            num_notifications = random.randint(2, 8)
            for _ in range(num_notifications):
                message, kind = random.choice(notification_messages)
                is_read = random.choice([True, False])
                created_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                
                cursor.execute('''
                    INSERT INTO notification 
                    (user_id, type, title, message, is_read, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, kind, message, f"Details about {message}", is_read, created_date))
        
        print(f"✓ Created sample notifications")
        
        # Create sample wishlist items
        wishlist_destinations = [
            ("Machu Picchu", "Cusco", "Peru", "https://example.com/machu-picchu.jpg", "adventure,history", 4.8),
            ("Great Wall of China", "Beijing", "China", "https://example.com/great-wall.jpg", "history,culture", 4.6),
            ("Northern Lights", "Reykjavik", "Iceland", "https://example.com/northern-lights.jpg", "nature,adventure", 4.9),
            ("Taj Mahal", "Agra", "India", "https://example.com/taj-mahal.jpg", "history,architecture", 4.7),
            ("Santorini", "Santorini", "Greece", "https://example.com/santorini.jpg", "romance,beach", 4.5),
            ("Safari", "Serengeti", "Tanzania", "https://example.com/safari.jpg", "wildlife,adventure", 4.8)
        ]
        
        for user_id in user_ids:
            num_wishlist = random.randint(3, 6)
            selected_items = random.sample(wishlist_destinations, min(num_wishlist, len(wishlist_destinations)))
            
            for title, city, country, image_url, tags, rating in selected_items:
                created_date = datetime.utcnow() - timedelta(days=random.randint(1, 90))
                
                cursor.execute('''
                    INSERT INTO wishlist_item 
                    (user_id, title, description, location, priority, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, title, f"Visit {title} in {city}", f"{city}, {country}", random.randint(1, 5), created_date))
        
        print(f"✓ Created sample wishlist items")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 Sample data creation completed successfully!")
        print("\nAdmin Login Details:")
        print(f"Email: {admin_email}")
        print("Password: admin123")
        print("\nYou can now access the admin dashboard at: http://localhost:5000/admin")
        
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_sample_data()
