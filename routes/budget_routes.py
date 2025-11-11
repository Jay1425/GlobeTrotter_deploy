from flask import Blueprint, jsonify, request
from travel_data_service import TravelDataService
from datetime import datetime

budget_routes = Blueprint('budget', __name__)
travel_service = TravelDataService()

@budget_routes.route('/api/budget/estimate', methods=['POST'])
def estimate_budget():
    """Estimate trip budget based on cities and duration"""
    try:
        data = request.get_json()
        cities = data.get('cities', [])
        duration_days = data.get('duration_days', 7)
        comfort_level = data.get('comfort_level', 'medium')
        
        budget = travel_service.calculate_trip_budget(
            cities=cities,
            duration_days=duration_days,
            comfort_level=comfort_level
        )
        
        return jsonify({
            'status': 'success',
            'data': budget
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@budget_routes.route('/api/costs/city/<city>/<country>', methods=['GET'])
def get_city_costs(city, country):
    """Get cost of living data for a specific city"""
    try:
        costs = travel_service.get_city_cost_of_living(city, country)
        return jsonify({
            'status': 'success',
            'data': costs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@budget_routes.route('/api/flights/price', methods=['GET'])
def get_flight_price():
    """Get estimated flight price between two cities"""
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        if not origin or not destination:
            return jsonify({
                'status': 'error',
                'message': 'Origin and destination are required'
            }), 400
            
        price = travel_service.get_flight_prices(origin, destination, date)
        return jsonify({
            'status': 'success',
            'data': {
                'price': price,
                'currency': 'INR',
                'origin': origin,
                'destination': destination,
                'date': date
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@budget_routes.route('/api/exchange-rates', methods=['GET'])
def get_exchange_rates():
    """Get current exchange rates"""
    try:
        rates = travel_service.get_exchange_rates()
        return jsonify({
            'status': 'success',
            'data': rates
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
