#!/usr/bin/env python3
"""
City Search Migration Script
Adds City and TripCity tables with sample data for city search functionality
"""

import sqlite3
import json
from datetime import datetime

def migrate_city_search():
    """Add city search tables and sample data"""
    conn = sqlite3.connect('globetrotter.db')
    cursor = conn.cursor()
    
    try:
        print("🌍 Starting City Search Migration...")
        
        # Create cities table
        print("📊 Creating cities table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                country VARCHAR(100) NOT NULL,
                region VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                cost_index VARCHAR(20) NOT NULL DEFAULT 'medium',
                cost_index_value INTEGER NOT NULL DEFAULT 50,
                popularity INTEGER NOT NULL DEFAULT 3,
                description TEXT,
                best_time VARCHAR(50),
                attractions TEXT,
                image_url VARCHAR(500),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for cities table
        print("📈 Creating indexes for cities...")
        indexes_cities = [
            "CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(name)",
            "CREATE INDEX IF NOT EXISTS idx_cities_country ON cities(country)",
            "CREATE INDEX IF NOT EXISTS idx_cities_region ON cities(region)",
            "CREATE INDEX IF NOT EXISTS idx_cities_cost_index ON cities(cost_index)",
            "CREATE INDEX IF NOT EXISTS idx_cities_popularity ON cities(popularity)",
            "CREATE INDEX IF NOT EXISTS idx_cities_created_at ON cities(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cities_country_cost ON cities(country, cost_index)",
            "CREATE INDEX IF NOT EXISTS idx_cities_popularity_name ON cities(popularity DESC, name ASC)"
        ]
        
        for index_sql in indexes_cities:
            cursor.execute(index_sql)
        
        # Create trip_cities table
        print("📊 Creating trip_cities table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trip_cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                city_id INTEGER,
                city_name VARCHAR(100) NOT NULL,
                country VARCHAR(100) NOT NULL,
                latitude FLOAT,
                longitude FLOAT,
                order_index INTEGER NOT NULL DEFAULT 0,
                arrival_date DATE,
                departure_date DATE,
                notes TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
                FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE SET NULL
            )
        ''')
        
        # Create indexes for trip_cities table
        print("📈 Creating indexes for trip_cities...")
        indexes_trip_cities = [
            "CREATE INDEX IF NOT EXISTS idx_trip_cities_trip_id ON trip_cities(trip_id)",
            "CREATE INDEX IF NOT EXISTS idx_trip_cities_city_id ON trip_cities(city_id)",
            "CREATE INDEX IF NOT EXISTS idx_trip_cities_order ON trip_cities(trip_id, order_index)",
            "CREATE INDEX IF NOT EXISTS idx_trip_cities_dates ON trip_cities(arrival_date, departure_date)"
        ]
        
        for index_sql in indexes_trip_cities:
            cursor.execute(index_sql)
        
        # Sample city data
        print("🏙️ Adding sample city data...")
        
        cities_data = [
            {
                'name': 'Mumbai',
                'country': 'India',
                'region': 'Maharashtra',
                'latitude': 19.0760,
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
                'description': 'India\'s capital city blending ancient heritage with modern dynamism',
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
                'cost_index': 'medium',
                'cost_index_value': 55,
                'popularity': 4,
                'description': 'Beach paradise with Portuguese heritage and vibrant nightlife',
                'best_time': 'Nov-Mar',
                'attractions': json.dumps(['Baga Beach', 'Old Goa Churches', 'Dudhsagar Falls', 'Calangute Beach']),
                'image_url': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=400&h=300&fit=crop'
            },
            {
                'name': 'Jaipur',
                'country': 'India',
                'region': 'Rajasthan',
                'latitude': 26.9124,
                'longitude': 75.7873,
                'cost_index': 'low',
                'cost_index_value': 45,
                'popularity': 4,
                'description': 'The Pink City famous for palaces, forts, and rich cultural heritage',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['Amber Fort', 'Hawa Mahal', 'City Palace', 'Jantar Mantar']),
                'image_url': 'https://images.unsplash.com/photo-1599661046827-dacde6976549?w=400&h=300&fit=crop'
            },
            {
                'name': 'Bangalore',
                'country': 'India',
                'region': 'Karnataka',
                'latitude': 12.9716,
                'longitude': 77.5946,
                'cost_index': 'medium',
                'cost_index_value': 70,
                'popularity': 4,
                'description': 'India\'s Silicon Valley with pleasant weather and vibrant pub culture',
                'best_time': 'Oct-Feb',
                'attractions': json.dumps(['Lalbagh Garden', 'Bangalore Palace', 'Cubbon Park', 'UB City Mall']),
                'image_url': 'https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=400&h=300&fit=crop'
            },
            {
                'name': 'Kolkata',
                'country': 'India',
                'region': 'West Bengal',
                'latitude': 22.5726,
                'longitude': 88.3639,
                'cost_index': 'low',
                'cost_index_value': 40,
                'popularity': 4,
                'description': 'The cultural capital of India, known for literature, art, and sweets',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['Victoria Memorial', 'Howrah Bridge', 'Dakshineswar Temple', 'Park Street']),
                'image_url': 'https://images.unsplash.com/photo-1558431382-27ca3c48f50f?w=400&h=300&fit=crop'
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
                'description': 'Gateway to South India with rich Tamil culture and beautiful beaches',
                'best_time': 'Nov-Feb',
                'attractions': json.dumps(['Marina Beach', 'Kapaleeshwarar Temple', 'Fort St. George', 'Mahabalipuram']),
                'image_url': 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=400&h=300&fit=crop'
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
                'description': 'The City of Lakes with stunning palaces and romantic ambiance',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['City Palace', 'Lake Pichola', 'Jag Mandir', 'Saheliyon Ki Bari']),
                'image_url': 'https://images.unsplash.com/photo-1605649487212-47bdab064cf4?w=400&h=300&fit=crop'
            },
            {
                'name': 'Varanasi',
                'country': 'India',
                'region': 'Uttar Pradesh',
                'latitude': 25.3176,
                'longitude': 82.9739,
                'cost_index': 'low',
                'cost_index_value': 35,
                'popularity': 4,
                'description': 'One of the world\'s oldest cities, spiritual center on the Ganges',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['Dashashwamedh Ghat', 'Kashi Vishwanath Temple', 'Sarnath', 'Ganga Aarti']),
                'image_url': 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=400&h=300&fit=crop'
            },
            {
                'name': 'Agra',
                'country': 'India',
                'region': 'Uttar Pradesh',
                'latitude': 27.1767,
                'longitude': 78.0081,
                'cost_index': 'low',
                'cost_index_value': 45,
                'popularity': 5,
                'description': 'Home to the iconic Taj Mahal and Mughal architectural wonders',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['Taj Mahal', 'Agra Fort', 'Mehtab Bagh', 'Fatehpur Sikri']),
                'image_url': 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=400&h=300&fit=crop'
            },
            {
                'name': 'Kochi',
                'country': 'India',
                'region': 'Kerala',
                'latitude': 9.9312,
                'longitude': 76.2673,
                'cost_index': 'medium',
                'cost_index_value': 50,
                'popularity': 4,
                'description': 'Queen of the Arabian Sea with backwaters and spice markets',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['Chinese Fishing Nets', 'Fort Kochi', 'Mattancherry Palace', 'Marine Drive']),
                'image_url': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=400&h=300&fit=crop'
            },
            {
                'name': 'Rishikesh',
                'country': 'India',
                'region': 'Uttarakhand',
                'latitude': 30.0869,
                'longitude': 78.2676,
                'cost_index': 'low',
                'cost_index_value': 30,
                'popularity': 4,
                'description': 'Yoga capital of the world nestled in the Himalayas',
                'best_time': 'Mar-Apr, Sep-Nov',
                'attractions': json.dumps(['Laxman Jhula', 'Ram Jhula', 'Triveni Ghat', 'Beatles Ashram']),
                'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop'
            },
            {
                'name': 'Hampi',
                'country': 'India',
                'region': 'Karnataka',
                'latitude': 15.3350,
                'longitude': 76.4600,
                'cost_index': 'low',
                'cost_index_value': 25,
                'popularity': 3,
                'description': 'UNESCO World Heritage site with ancient ruins and boulder landscapes',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['Virupaksha Temple', 'Hampi Bazaar', 'Vittala Temple', 'Matanga Hill']),
                'image_url': 'https://images.unsplash.com/photo-1582719471384-894fbb16e074?w=400&h=300&fit=crop'
            },
            {
                'name': 'Manali',
                'country': 'India',
                'region': 'Himachal Pradesh',
                'latitude': 32.2396,
                'longitude': 77.1887,
                'cost_index': 'medium',
                'cost_index_value': 60,
                'popularity': 4,
                'description': 'Hill station paradise with snow-capped mountains and adventure sports',
                'best_time': 'Mar-Jun, Sep-Nov',
                'attractions': json.dumps(['Solang Valley', 'Rohtang Pass', 'Hadimba Temple', 'Old Manali']),
                'image_url': 'https://images.unsplash.com/photo-1626618012641-bfbca5a31239?w=400&h=300&fit=crop'
            },
            {
                'name': 'Pushkar',
                'country': 'India',
                'region': 'Rajasthan',
                'latitude': 26.4899,
                'longitude': 74.5513,
                'cost_index': 'low',
                'cost_index_value': 35,
                'popularity': 3,
                'description': 'Sacred lake town famous for camel fair and spiritual atmosphere',
                'best_time': 'Oct-Mar',
                'attractions': json.dumps(['Pushkar Lake', 'Brahma Temple', 'Savitri Temple', 'Camel Safari']),
                'image_url': 'https://images.unsplash.com/photo-1624025902058-a7511ac0396c?w=400&h=300&fit=crop'
            }
        ]
        
        # Check if cities already exist
        cursor.execute("SELECT COUNT(*) FROM cities")
        existing_count = cursor.fetchone()[0]
        
        if existing_count == 0:
            # Insert sample cities
            for city in cities_data:
                cursor.execute('''
                    INSERT INTO cities (
                        name, country, region, latitude, longitude, cost_index, cost_index_value,
                        popularity, description, best_time, attractions, image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    city['name'], city['country'], city['region'], city['latitude'], city['longitude'],
                    city['cost_index'], city['cost_index_value'], city['popularity'], 
                    city['description'], city['best_time'], city['attractions'], city['image_url']
                ))
            
            print(f"✅ Added {len(cities_data)} sample cities")
        else:
            print(f"ℹ️ Cities table already has {existing_count} entries, skipping sample data")
        
        conn.commit()
        print("✅ City Search Migration completed successfully!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM cities")
        total_cities = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM trip_cities")
        total_trip_cities = cursor.fetchone()[0]
        
        print(f"\n📊 Migration Summary:")
        print(f"   Cities: {total_cities}")
        print(f"   Trip Cities: {total_trip_cities}")
        print(f"   Tables created: cities, trip_cities")
        print(f"   Indexes created: 12 total")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during migration: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_city_search()
