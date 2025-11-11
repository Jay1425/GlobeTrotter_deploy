import unittest
from app import app
from models import db, User, Trip
import json

class TestBudgetRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test user
            user = User(
                email='test@test.com',
                first_name='Test',
                last_name='User'
            )
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Create test trip
            trip = Trip(
                user_id=user.id,
                title='Test Trip',
                status='planned'
            )
            db.session.add(trip)
            db.session.commit()
            
            self.user = user
            self.trip = trip
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def login(self):
        with self.client.session_transaction() as session:
            session['user_email'] = 'test@test.com'
    
    def test_budget_estimate_requires_auth(self):
        """Test that budget estimate endpoint requires authentication"""
        response = self.client.post('/api/budget/estimate', 
            json={
                'cities': ['Paris'],
                'duration_days': 7
            })
        self.assertEqual(response.status_code, 401)
    
    def test_budget_estimate_calculation(self):
        """Test budget estimation calculation"""
        self.login()
        response = self.client.post('/api/budget/estimate',
            json={
                'cities': [
                    {'city': 'Paris', 'country': 'France', 'days': 4}
                ],
                'duration_days': 4,
                'comfort_level': 'medium'
            })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('data' in data)
        self.assertTrue('total_budget' in data['data'])
        self.assertTrue(data['data']['total_budget'] > 0)
    
    def test_city_costs_endpoint(self):
        """Test getting city costs"""
        self.login()
        response = self.client.get('/api/costs/city/Paris/France')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('data' in data)
        self.assertTrue(isinstance(data['data'], dict))
    
    def test_flight_price_endpoint(self):
        """Test getting flight prices"""
        self.login()
        response = self.client.get('/api/flights/price?origin=Paris&destination=London')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('data' in data)
        self.assertTrue('price' in data['data'])
    
    def test_exchange_rates_endpoint(self):
        """Test getting exchange rates"""
        self.login()
        response = self.client.get('/api/exchange-rates')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('data' in data)
        self.assertTrue(isinstance(data['data'], dict))

if __name__ == '__main__':
    unittest.main()
