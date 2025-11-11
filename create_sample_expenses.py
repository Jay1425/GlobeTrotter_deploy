#!/usr/bin/env python3
"""
Create sample expense data for Indian trips
"""

from app import app, db, User, Trip, TripExpense, TripDestination
from datetime import datetime, timedelta, date
import random

def create_sample_expenses():
    with app.app_context():
        # Check if expenses already exist
        existing_expenses = TripExpense.query.count()
        if existing_expenses > 0:
            print(f"Expenses already exist: {existing_expenses} records")
            return
        
        # Get all trips
        trips = Trip.query.all()
        print(f"Found {len(trips)} trips to add expenses to")
        
        # Expense categories with typical amounts for Indian trips
        expense_categories = {
            'accommodation': {'min': 1000, 'max': 8000, 'descriptions': ['Hotel stay', 'Resort booking', 'Homestay', 'Guest house']},
            'meals': {'min': 300, 'max': 2000, 'descriptions': ['Restaurant dinner', 'Street food', 'Local cuisine', 'Breakfast buffet']},
            'transport': {'min': 500, 'max': 5000, 'descriptions': ['Bus fare', 'Train tickets', 'Auto rickshaw', 'Cab ride', 'Flight booking']},
            'activities': {'min': 200, 'max': 3000, 'descriptions': ['Sightseeing tour', 'Adventure sports', 'Museum entry', 'Boat ride']},
            'shopping': {'min': 500, 'max': 4000, 'descriptions': ['Souvenirs', 'Local handicrafts', 'Clothing', 'Gifts']},
            'other': {'min': 100, 'max': 1500, 'descriptions': ['Miscellaneous', 'Emergency expense', 'Tips', 'Phone recharge']}
        }
        
        total_expenses_created = 0
        
        for trip in trips:
            # Create 5-15 expenses per trip
            num_expenses = random.randint(5, 15)
            trip_start = trip.start_date or date.today()
            trip_end = trip.end_date or (trip_start + timedelta(days=7))
            
            print(f"Creating {num_expenses} expenses for trip: {trip.title}")
            
            for _ in range(num_expenses):
                # Random category
                category = random.choice(list(expense_categories.keys()))
                category_data = expense_categories[category]
                
                # Random amount within category range
                amount = random.randint(category_data['min'], category_data['max'])
                
                # Random description
                description = random.choice(category_data['descriptions'])
                
                # Random date during trip
                if trip_start and trip_end:
                    days_diff = (trip_end - trip_start).days
                    if days_diff > 0:
                        random_days = random.randint(0, days_diff)
                        expense_date = trip_start + timedelta(days=random_days)
                    else:
                        expense_date = trip_start
                else:
                    expense_date = date.today()
                
                # Get random destination for this trip
                destinations = list(trip.destinations)
                destination_id = random.choice(destinations).id if destinations else None
                
                expense = TripExpense(
                    trip_id=trip.id,
                    category=category,
                    amount=amount,
                    description=description,
                    expense_date=expense_date,
                    destination_id=destination_id
                )
                
                db.session.add(expense)
                total_expenses_created += 1
        
        db.session.commit()
        print(f"✅ Created {total_expenses_created} sample expenses!")
        
        # Print summary
        total_amount = db.session.query(db.func.sum(TripExpense.amount)).scalar() or 0
        print(f"Total expense amount: ₹{total_amount:,.0f}")
        
        # Category breakdown
        print("\nExpense breakdown by category:")
        categories = db.session.query(
            TripExpense.category,
            db.func.sum(TripExpense.amount).label('total'),
            db.func.count(TripExpense.id).label('count')
        ).group_by(TripExpense.category).all()
        
        for cat in categories:
            print(f"  {cat.category.title()}: ₹{cat.total:,.0f} ({cat.count} expenses)")

if __name__ == '__main__':
    create_sample_expenses()
