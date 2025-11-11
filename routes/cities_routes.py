from flask import Blueprint, jsonify, request
import requests
from datetime import datetime
import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

cities_routes = Blueprint('cities', __name__)

# Cache for city data to minimize API calls (short-term, in-memory only)
city_cache = {}
CACHE_DURATION = 3600  # 1 hour in seconds

async def fetch_exchange_rates():
    """Fetch current exchange rates from ExchangeRate-API (free tier)"""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return data.get('rates', {})
    except Exception as e:
        print(f"Error fetching exchange rates: {str(e)}")
        return {}

# Cache for city data to minimize API calls
city_cache = {}

async def fetch_city_info(city_name):
    """Fetch city information from Wikidata API (free)"""
    try:
        query = f"""
        SELECT ?city ?population ?country ?countryLabel ?elevation ?timezone
        WHERE {{
            ?city rdfs:label "{city_name}"@en;
                  wdt:P1082 ?population;
                  wdt:P17 ?country.
            OPTIONAL {{ ?city wdt:P2044 ?elevation }}
            OPTIONAL {{ ?city wdt:P421 ?timezone }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        url = "https://query.wikidata.org/sparql"
        headers = {'Accept': 'application/json'}
        params = {'query': query, 'format': 'json'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                results = data.get('results', {}).get('bindings', [])
                if results:
                    return results[0]
        return {}
    except Exception as e:
        print(f"Error fetching city info: {str(e)}")
        return {}

async def fetch_cost_estimates(city_name, country_code):
    """Get cost estimates from multiple free sources"""
    try:
        # Use World Bank Development Indicators API to get GDP per capita
        wb_url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.PCAP.CD?format=json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(wb_url) as response:
                data = await response.json()
                
        gdp_per_capita = 0
        if data and len(data) > 1 and data[1]:
            gdp_per_capita = float(data[1][0].get('value', 0))
        
        # Calculate cost categories based on GDP per capita
        costs = {
            "budget": {},
            "mid": {},
            "luxury": {}
        }
        
        if gdp_per_capita > 0:
            cost_multipliers = {
                "budget": 0.5,
                "mid": 1.0,
                "luxury": 2.5
            }
            
            base_costs = {
                "hotel": gdp_per_capita / 365,  # Daily hotel cost
                "meal": gdp_per_capita / 1500,  # Average meal cost
                "transport": gdp_per_capita / 3000,  # Daily transport cost
                "activities": gdp_per_capita / 2000  # Daily activities cost
            }
            
            for style, multiplier in cost_multipliers.items():
                costs[style] = {
                    category: base * multiplier
                    for category, base in base_costs.items()
                }
        
        return costs
    except Exception as e:
        print(f"Error fetching cost estimates: {str(e)}")
        return {}

@cities_routes.route('/api/city-data')
def get_city_data():
    """Get detailed information about a city"""
    try:
        city = request.args.get('city')
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        travel_style = request.args.get('style', 'mid')  # budget, mid, luxury
        
        if not city:
            return jsonify({"error": "City name is required"}), 400
            
        # Check cache first
        cache_key = f"{city}_{lat}_{lng}_{travel_style}"
        if cache_key in city_cache:
            return jsonify(city_cache[cache_key])
            
        # Get city details
        city_data = {
            "name": city,
            "id": f"city_{lat}_{lng}",
            "location": {
                "lat": float(lat),
                "lng": float(lng)
            }
        }
        
        # Get weather data
        try:
            weather_api_key = os.getenv('WEATHER_API_KEY')
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={weather_api_key}"
            weather_response = requests.get(weather_url)
            if weather_response.ok:
                weather_data = weather_response.json()
                city_data["weather"] = {
                    "temp": weather_data["main"]["temp"] - 273.15,  # Convert to Celsius
                    "description": weather_data["weather"][0]["description"],
                    "icon": weather_data["weather"][0]["icon"]
                }
        except Exception as e:
            print(f"Weather API error: {str(e)}")
            
        # Get cost data from our local database
        cost_info = get_city_cost_index(city)
        city_data["costIndex"] = cost_info["cost_index"]
        city_data["relativeValue"] = cost_info["relative_value"]
        
        # Get detailed costs based on travel style
        city_data["costs"] = get_relative_costs(cost_info["cost_index"], travel_style)
            
        # Get best time to visit based on climate data
        try:
            # This would typically come from a climate API or database
            # For now, use a simple hemisphere-based calculation
            hemisphere = "Northern" if float(lat) > 0 else "Southern"
            current_month = datetime.now().month
            
            if hemisphere == "Northern":
                if 4 <= current_month <= 10:
                    city_data["bestTime"] = "Apr-Oct"
                else:
                    city_data["bestTime"] = "May-Sep"
            else:
                if 10 <= current_month <= 3:
                    city_data["bestTime"] = "Oct-Mar"
                else:
                    city_data["bestTime"] = "Nov-Feb"
        except Exception as e:
            print(f"Climate calculation error: {str(e)}")
            city_data["bestTime"] = "Year-round"
            
        # Get city image from Unsplash API
        try:
            unsplash_api_key = os.getenv('UNSPLASH_API_KEY')
            unsplash_url = f"https://api.unsplash.com/photos/random?query={city}+cityscape&client_id={unsplash_api_key}"
            unsplash_response = requests.get(unsplash_url)
            if unsplash_response.ok:
                image_data = unsplash_response.json()
                city_data["imageUrl"] = image_data["urls"]["regular"]
        except Exception as e:
            print(f"Unsplash API error: {str(e)}")
            city_data["imageUrl"] = f"https://source.unsplash.com/800x500/?{city}"
            
        # Add popularity score (could be based on various factors)
        city_data["popularity"] = "Very Popular"  # This could be dynamic based on data
        city_data["rating"] = 4.5  # This could be from user reviews
        
        # Cache the results
        city_cache[cache_key] = city_data
        
        return jsonify(city_data)
        
    except Exception as e:
        print(f"City data error: {str(e)}")
        return jsonify({"error": "Failed to fetch city data"}), 500

@cities_routes.route('/api/city-suggestions')
def get_city_suggestions():
    """Get suggested cities based on search criteria"""
    try:
        query = request.args.get('q', '').lower()
        region = request.args.get('region', '')
        cost_preference = request.args.get('cost', '')  # low, medium, high, very-high
        
        suggestions = []
        
        # Search through our city costs data
        for region_name, region_data in city_costs_data["cost_indices"].items():
            if region and region.lower() != region_name.lower():
                continue
                
            for subregion, cities in region_data.items():
                for city_name, city_info in cities.items():
                    if query and query not in city_name.lower():
                        continue
                        
                    if cost_preference and cost_preference != city_info["cost_index"].lower().replace(" ", "-"):
                        continue
                        
                    suggestions.append({
                        "name": city_name,
                        "region": region_name,
                        "subregion": subregion,
                        "rating": min(5, 3.5 + (city_info["relative_value"] / 100 * 1.5)),
                        "costIndex": city_info["cost_index"],
                        "popularity": "Very Popular" if city_info["relative_value"] >= 70 else "Popular",
                        "imageUrl": f"https://source.unsplash.com/800x500/?{city_name}"
                    })
        
        # Sort by rating
        suggestions.sort(key=lambda x: x["rating"], reverse=True)
        
        return jsonify({
            "cities": suggestions[:20],  # Limit to top 20 results
            "total": len(suggestions)
        })
        
    except Exception as e:
        print(f"City suggestions error: {str(e)}")
        return jsonify({"error": "Failed to get city suggestions"}), 500
