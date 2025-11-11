import requests
from typing import Dict, List, Optional
import json
from datetime import datetime
import os
from functools import lru_cache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys (replace with your actual API keys)
NUMBEO_API_KEY = os.getenv('NUMBEO_API_KEY', 'your_numbeo_api_key')
EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY', 'your_exchange_rate_api_key')
AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY', 'your_amadeus_api_key')

class TravelDataService:
    """Service to fetch and process travel-related data from various APIs"""
    
    def __init__(self):
        self.base_currency = 'INR'
        self._load_cached_data()

    def _load_cached_data(self):
        """Load cached data from JSON files if they exist"""
        try:
            with open('data/city_costs.json', 'r') as f:
                self.city_costs = json.load(f)
        except FileNotFoundError:
            self.city_costs = {}
            
        try:
            with open('data/exchange_rates.json', 'r') as f:
                self.exchange_rates = json.load(f)
        except FileNotFoundError:
            self.exchange_rates = {}

    @lru_cache(maxsize=100)
    def get_city_cost_of_living(self, city: str, country: str) -> Dict:
        """Fetch cost of living data from Numbeo API"""
        try:
            url = f"https://www.numbeo.com/api/city_prices"
            params = {
                "api_key": NUMBEO_API_KEY,
                "city": city,
                "country": country
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            # Extract relevant costs
            costs = {
                "hotel_cost": self._extract_cost(data, "Hotel, Single Room"),
                "meal_cost": self._extract_cost(data, "Meal, Inexpensive Restaurant"),
                "transport_cost": self._extract_cost(data, "Transportation, Monthly Pass"),
                "coffee_cost": self._extract_cost(data, "Coffee"),
                "cost_index": data.get("cost_index", 100)
            }
            
            # Cache the data
            self.city_costs[f"{city}, {country}"] = costs
            self._save_cached_data()
            
            return costs
        except Exception as e:
            logger.error(f"Error fetching cost data for {city}, {country}: {str(e)}")
            return self._get_fallback_costs()

    def _extract_cost(self, data: Dict, item_name: str) -> float:
        """Extract cost for a specific item from Numbeo data"""
        try:
            items = data.get("prices", [])
            item = next((item for item in items if item["item_name"] == item_name), None)
            return item["average_price"] if item else 0
        except Exception:
            return 0

    def _get_fallback_costs(self) -> Dict:
        """Return fallback cost data when API fails"""
        return {
            "hotel_cost": 2500,  # Average hotel cost in INR
            "meal_cost": 300,    # Average meal cost in INR
            "transport_cost": 100,  # Average daily transport cost in INR
            "coffee_cost": 150,   # Average coffee cost in INR
            "cost_index": 100     # Base cost index
        }

    @lru_cache(maxsize=1)
    def get_exchange_rates(self) -> Dict:
        """Fetch latest exchange rates"""
        try:
            url = "https://api.exchangerate-api.com/v4/latest/INR"
            response = requests.get(url)
            data = response.json()
            
            # Cache the data
            self.exchange_rates = data["rates"]
            self._save_cached_data()
            
            return self.exchange_rates
        except Exception as e:
            logger.error(f"Error fetching exchange rates: {str(e)}")
            return self.exchange_rates or {"USD": 0.012, "EUR": 0.011, "GBP": 0.0096}

    def calculate_trip_budget(self, cities: List[Dict], duration_days: int, 
                            comfort_level: str = "medium") -> Dict:
        """
        Calculate estimated trip budget based on cities, duration, and comfort level
        comfort_level can be "budget", "medium", or "luxury"
        """
        multipliers = {
            "budget": 0.7,
            "medium": 1.0,
            "luxury": 1.8
        }
        
        total_budget = 0
        cost_breakdown = {
            "accommodation": 0,
            "food": 0,
            "transport": 0,
            "activities": 0,
            "misc": 0
        }

        multiplier = multipliers.get(comfort_level, 1.0)
        
        for city_data in cities:
            city = city_data["city"]
            country = city_data["country"]
            days = city_data.get("days", duration_days // len(cities))
            
            costs = self.get_city_cost_of_living(city, country)
            
            # Calculate daily costs
            daily_hotel = costs["hotel_cost"] * multiplier
            daily_food = costs["meal_cost"] * 3 * multiplier  # 3 meals per day
            daily_transport = costs["transport_cost"] / 30 * multiplier  # Convert monthly to daily
            daily_activities = (costs["hotel_cost"] * 0.3) * multiplier  # Estimate activities as 30% of hotel cost
            daily_misc = (costs["coffee_cost"] * 2) * multiplier  # Miscellaneous expenses
            
            # Add to total for this city
            cost_breakdown["accommodation"] += daily_hotel * days
            cost_breakdown["food"] += daily_food * days
            cost_breakdown["transport"] += daily_transport * days
            cost_breakdown["activities"] += daily_activities * days
            cost_breakdown["misc"] += daily_misc * days
            
            total_budget += (daily_hotel + daily_food + daily_transport + 
                           daily_activities + daily_misc) * days

        return {
            "total_budget": round(total_budget),
            "cost_breakdown": {k: round(v) for k, v in cost_breakdown.items()},
            "daily_average": round(total_budget / duration_days),
            "currency": "INR",
            "comfort_level": comfort_level
        }

    def get_flight_prices(self, origin: str, destination: str, date: str) -> Optional[float]:
        """Fetch flight prices using Amadeus API"""
        try:
            # This would normally use the Amadeus API
            # For now, return an estimated price based on distance
            base_price = 5000  # Base price in INR
            return base_price
        except Exception as e:
            logger.error(f"Error fetching flight prices: {str(e)}")
            return None

    def _save_cached_data(self):
        """Save cached data to JSON files"""
        os.makedirs('data', exist_ok=True)
        
        with open('data/city_costs.json', 'w') as f:
            json.dump(self.city_costs, f)
            
        with open('data/exchange_rates.json', 'w') as f:
            json.dump(self.exchange_rates, f)

# Example usage
if __name__ == "__main__":
    service = TravelDataService()
    
    # Example trip
    cities = [
        {"city": "Paris", "country": "France", "days": 4},
        {"city": "Rome", "country": "Italy", "days": 3},
        {"city": "Barcelona", "country": "Spain", "days": 3}
    ]
    
    budget = service.calculate_trip_budget(cities, duration_days=10, comfort_level="medium")
    print(json.dumps(budget, indent=2))
