#!/usr/bin/env python3
"""
Flask ORM City Data Migration
Properly creates city data through Flask's SQLAlchemy ORM for compatibility
"""

import app
from models import db, City
import json

def create_city_data():
    """Create comprehensive city data through Flask ORM"""
    
    cities_data = [
        {
            'name': 'Mumbai',
            'country': 'India',
            'region': 'Maharashtra',
            'latitude': 19.076,
            'longitude': 72.8777,
            'cost_index': 'medium',
            'cost_index_value': 65,
            'popularity': 5,
            'description': 'The financial capital of India, known for Bollywood and vibrant street life',
            'best_time': 'Oct-Mar',
            'attractions': json.dumps(['Gateway of India', 'Marine Drive', 'Bollywood Studios', 'Chhatrapati Shivaji Terminus']),
            'image_url': 'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=400&h=300&fit=crop'
        },
        {
            'name': 'Delhi',
            'country': 'India',
            'region': 'Delhi',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'cost_index': 'medium',
            'cost_index_value': 60,
            'popularity': 5,
            'description': 'The capital city rich in history, culture, and political significance',
            'best_time': 'Oct-Mar',
            'attractions': json.dumps(['Red Fort', 'India Gate', 'Lotus Temple', 'Qutub Minar']),
            'image_url': 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=400&h=300&fit=crop'
        },
        {
            'name': 'Goa',
            'country': 'India',
            'region': 'Goa',
            'latitude': 15.2993,
            'longitude': 74.1240,
            'cost_index': 'low',
            'cost_index_value': 45,
            'popularity': 4,
            'description': 'Famous for its beautiful beaches, vibrant nightlife, and Portuguese heritage',
            'best_time': 'Nov-Feb',
            'attractions': json.dumps(['Baga Beach', 'Basilica of Bom Jesus', 'Dudhsagar Falls', 'Anjuna Beach']),
            'image_url': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=400&h=300&fit=crop'
        },
        {
            'name': 'Jaipur',
            'country': 'India',
            'region': 'Rajasthan',
            'latitude': 26.9124,
            'longitude': 75.7873,
            'cost_index': 'low',
            'cost_index_value': 40,
            'popularity': 4,
            'description': 'The Pink City known for its magnificent palaces, forts, and royal heritage',
            'best_time': 'Oct-Mar',
            'attractions': json.dumps(['Hawa Mahal', 'City Palace', 'Amber Fort', 'Jantar Mantar']),
            'image_url': 'https://images.unsplash.com/photo-1599661046251-bfb9465b4c44?w=400&h=300&fit=crop'
        },
        {
            'name': 'Kerala',
            'country': 'India',
            'region': 'Kerala',
            'latitude': 10.8505,
            'longitude': 76.2711,
            'cost_index': 'low',
            'cost_index_value': 35,
            'popularity': 4,
            'description': 'God\'s Own Country with backwaters, hill stations, and spice plantations',
            'best_time': 'Sep-Mar',
            'attractions': json.dumps(['Backwaters', 'Munnar Hill Station', 'Periyar Wildlife Sanctuary', 'Fort Kochi']),
            'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop'
        },
        {
            'name': 'Agra',
            'country': 'India',
            'region': 'Uttar Pradesh',
            'latitude': 27.1767,
            'longitude': 78.0081,
            'cost_index': 'low',
            'cost_index_value': 35,
            'popularity': 5,
            'description': 'Home to the iconic Taj Mahal and rich Mughal architecture',
            'best_time': 'Oct-Mar',
            'attractions': json.dumps(['Taj Mahal', 'Agra Fort', 'Fatehpur Sikri', 'Mehtab Bagh']),
            'image_url': 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=400&h=300&fit=crop'
        },
        {
            'name': 'Bangalore',
            'country': 'India',
            'region': 'Karnataka',
            'latitude': 12.9716,
            'longitude': 77.5946,
            'cost_index': 'medium',
            'cost_index_value': 55,
            'popularity': 4,
            'description': 'The Silicon Valley of India with pleasant weather and modern amenities',
            'best_time': 'Oct-Feb',
            'attractions': json.dumps(['Lalbagh Botanical Garden', 'Bangalore Palace', 'Cubbon Park', 'ISKCON Temple']),
            'image_url': 'https://images.unsplash.com/photo-1596176530529-78163a4f6d46?w=400&h=300&fit=crop'
        },
        {
            'name': 'Udaipur',
            'country': 'India',
            'region': 'Rajasthan',
            'latitude': 24.5854,
            'longitude': 73.7125,
            'cost_index': 'medium',
            'cost_index_value': 50,
            'popularity': 4,
            'description': 'The City of Lakes known for its romantic palaces and heritage hotels',
            'best_time': 'Oct-Mar',
            'attractions': json.dumps(['City Palace', 'Lake Pichola', 'Jag Mandir', 'Saheliyon Ki Bari']),
            'image_url': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop'
        },
        {
            'name': 'Varanasi',
            'country': 'India',
            'region': 'Uttar Pradesh',
            'latitude': 25.3176,
            'longitude': 82.9739,
            'cost_index': 'low',
            'cost_index_value': 30,
            'popularity': 4,
            'description': 'One of the oldest cities in the world, spiritual capital of India',
            'best_time': 'Oct-Mar',
            'attractions': json.dumps(['Kashi Vishwanath Temple', 'Ganges Ghats', 'Sarnath', 'Ramnagar Fort']),
            'image_url': 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=400&h=300&fit=crop'
        },
        {
            'name': 'Rishikesh',
            'country': 'India',
            'region': 'Uttarakhand',
            'latitude': 30.0869,
            'longitude': 78.2676,
            'cost_index': 'low',
            'cost_index_value': 25,
            'popularity': 3,
            'description': 'The Yoga Capital of the World nestled in the Himalayas',
            'best_time': 'Sep-Apr',
            'attractions': json.dumps(['Laxman Jhula', 'Ram Jhula', 'Beatles Ashram', 'River Rafting']),
            'image_url': 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a96?w=400&h=300&fit=crop'
        },
        {
            'name': 'Chennai',
            'country': 'India',
            'region': 'Tamil Nadu',
            'latitude': 13.0827,
            'longitude': 80.2707,
            'cost_index': 'medium',
            'cost_index_value': 55,
            'popularity': 3,
            'description': 'The Detroit of India known for its beaches, temples, and cultural heritage',
            'best_time': 'Nov-Feb',
            'attractions': json.dumps(['Marina Beach', 'Kapaleeshwarar Temple', 'Fort St. George', 'Mahabalipuram']),
            'image_url': 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=400&h=300&fit=crop'
        },
        {
            'name': 'Kolkata',
            'country': 'India',
            'region': 'West Bengal',
            'latitude': 22.5726,
            'longitude': 88.3639,
            'cost_index': 'low',
            'cost_index_value': 35,
            'popularity': 3,
            'description': 'The Cultural Capital of India with rich literary and artistic heritage',
            'best_time': 'Oct-Mar',
            'attractions': json.dumps(['Victoria Memorial', 'Howrah Bridge', 'Dakshineswar Temple', 'Park Street']),
            'image_url': 'https://images.unsplash.com/photo-1558431382-27e303142255?w=400&h=300&fit=crop'
        },
        {
            'name': 'Hyderabad',
            'country': 'India',
            'region': 'Telangana',
            'latitude': 17.3850,
            'longitude': 78.4867,
            'cost_index': 'medium',
            'cost_index_value': 50,
            'popularity': 3,
            'description': 'The City of Pearls known for its biryani, pearls, and IT industry',
            'best_time': 'Oct-Feb',
            'attractions': json.dumps(['Charminar', 'Golconda Fort', 'Ramoji Film City', 'Hussain Sagar Lake']),
            'image_url': 'https://images.unsplash.com/photo-1595211877493-41a4e5cd4b23?w=400&h=300&fit=crop'
        },
        {
            'name': 'Pune',
            'country': 'India',
            'region': 'Maharashtra',
            'latitude': 18.5204,
            'longitude': 73.8567,
            'cost_index': 'medium',
            'cost_index_value': 55,
            'popularity': 3,
            'description': 'The Oxford of the East with pleasant climate and educational institutions',
            'best_time': 'Oct-Feb',
            'attractions': json.dumps(['Shaniwar Wada', 'Aga Khan Palace', 'Sinhagad Fort', 'Osho Ashram']),
            'image_url': 'https://images.unsplash.com/photo-1605640840605-14ac1855827b?w=400&h=300&fit=crop'
        },
        {
            'name': 'Ahmedabad',
            'country': 'India',
            'region': 'Gujarat',
            'latitude': 23.0225,
            'longitude': 72.5714,
            'cost_index': 'low',
            'cost_index_value': 40,
            'popularity': 3,
            'description': 'UNESCO World Heritage City known for its textile industry and heritage',
            'best_time': 'Nov-Feb',
            'attractions': json.dumps(['Sabarmati Ashram', 'Adalaj Stepwell', 'Akshardham Temple', 'Kankaria Lake']),
            'image_url': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop'
        }
    ]
    
    return cities_data

def migrate_cities():
    """Run the Flask ORM city migration"""
    
    with app.app.app_context():
        print("🌍 Starting Flask ORM City Migration...")
        
        # Ensure tables exist
        db.create_all()
        
        # Clear existing cities
        existing_count = City.query.count()
        if existing_count > 0:
            print(f"🧹 Removing {existing_count} existing cities...")
            City.query.delete()
            db.session.commit()
        
        # Add new cities
        cities_data = create_city_data()
        print(f"🏙️ Adding {len(cities_data)} cities...")
        
        for city_data in cities_data:
            city = City(**city_data)
            db.session.add(city)
        
        try:
            db.session.commit()
            
            # Verify the data
            final_count = City.query.count()
            print(f"✅ Successfully added {final_count} cities!")
            
            # Test search functionality
            print("\n🔍 Testing search functionality...")
            mumbai_results = City.search_cities(query='Mumbai')
            print(f"   Search 'Mumbai': {len(mumbai_results)} results")
            
            medium_cost = City.search_cities(cost_filter='medium')
            print(f"   Medium cost cities: {len(medium_cost)} results")
            
            india_cities = City.search_cities(country='India')
            print(f"   Cities in India: {len(india_cities)} results")
            
            print("\n📊 Sample cities:")
            for city in City.query.limit(3):
                print(f"   - {city.name}, {city.country} (Cost: {city.cost_index}, Pop: {city.popularity})")
                print(f"     Coordinates: ({city.latitude}, {city.longitude})")
            
            print("\n✅ Flask ORM City Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_cities()
