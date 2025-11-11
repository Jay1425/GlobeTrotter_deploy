from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(32), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    state = db.Column(db.String(120), nullable=True)
    country = db.Column(db.String(120), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    travel_preferences = db.Column(db.Text, nullable=True)  # JSON string of preferences
    profile_picture = db.Column(db.String(500), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Admin role
    last_login = db.Column(db.DateTime, nullable=True)  # Track last login for analytics
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)  # Track active users
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)  # Email verification status
    otp_code = db.Column(db.String(6), nullable=True)  # OTP for email verification
    otp_expiry = db.Column(db.DateTime, nullable=True)  # OTP expiration time
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        """Generate a password reset token that expires in 1 hour"""
        import secrets
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return token

    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        return (self.reset_token == token and 
                self.reset_token_expiry and 
                datetime.utcnow() < self.reset_token_expiry)
    
    def generate_otp(self):
        """Generate a 6-digit OTP for email verification"""
        import random
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_code = otp
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=10)  # OTP expires in 10 minutes
        return otp
    
    def verify_otp(self, otp):
        """Verify if the OTP is valid and not expired"""
        return (self.otp_code == otp and 
                self.otp_expiry and 
                datetime.utcnow() < self.otp_expiry)
    
    def clear_otp(self):
        """Clear OTP after successful verification"""
        self.otp_code = None
        self.otp_expiry = None

    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)  # Add index for searching
    start_date = db.Column(db.Date, nullable=True, index=True)  # Add index for sorting by date
    end_date = db.Column(db.Date, nullable=True, index=True)  # Add index for sorting by date
    status = db.Column(db.String(20), nullable=False, default="planned", index=True)  # Add index for filtering
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)  # Add index for sorting
    budget = db.Column(db.Float, nullable=True, index=True)  # Add budget field with index
    priority = db.Column(db.Integer, default=0, nullable=False, index=True)  # Add priority for sorting

    user = db.relationship("User", backref=db.backref("trips", lazy="dynamic", order_by="Trip.created_at.desc()"))

    def __repr__(self):
        return f'<Trip {self.title}>'
    
    @classmethod
    def search_trips(cls, user_id, query=None, status=None, limit=None, offset=0, order_by='created_at', order_dir='desc'):
        """Fast search with optimized queries"""
        # Base query without problematic eager loading
        base_query = cls.query.filter_by(user_id=user_id)
        
        # Apply text search using database full-text search capabilities
        if query:
            search_filter = cls.title.ilike(f'%{query}%')
            base_query = base_query.filter(search_filter)
        
        # Apply status filter
        if status:
            base_query = base_query.filter(cls.status == status)
        
        # Apply sorting
        if order_by == 'title':
            order_column = cls.title
        elif order_by == 'start_date':
            order_column = cls.start_date
        elif order_by == 'status':
            order_column = cls.status
        elif order_by == 'priority':
            order_column = cls.priority
        else:
            order_column = cls.created_at
            
        if order_dir == 'asc':
            base_query = base_query.order_by(order_column.asc())
        else:
            base_query = base_query.order_by(order_column.desc())
        
        # Apply pagination
        if offset:
            base_query = base_query.offset(offset)
        if limit:
            base_query = base_query.limit(limit)
            
        return base_query.all()


class TripDestination(db.Model):
    __tablename__ = "trip_destinations"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)  # Add index for searching
    city = db.Column(db.String(120), nullable=True, index=True)  # Add index for searching
    country = db.Column(db.String(120), nullable=True, index=True)  # Add index for searching
    order_index = db.Column(db.Integer, default=0, nullable=False, index=True)  # Add index for ordering
    sequence = db.Column(db.Integer, default=0, nullable=False, index=True)  # Add sequence field
    budget_allocated = db.Column(db.Float, nullable=True)  # Add budget allocation per destination
    budget = db.Column(db.Float, nullable=True)  # Section budget
    date = db.Column(db.Date, nullable=True)  # Add date for when to visit this destination
    date_range = db.Column(db.String(100), nullable=True)  # Date range string
    duration = db.Column(db.String(50), nullable=True)  # Add duration to stay
    description = db.Column(db.Text, nullable=True)  # Add description
    notes = db.Column(db.Text, nullable=True)  # Activities and other notes as JSON
    city_id = db.Column(db.Integer, nullable=True, index=True)  # Add city_id for relations

    trip = db.relationship("Trip", backref=db.backref("destinations", lazy="dynamic", order_by="TripDestination.order_index.asc()"))

    def __repr__(self):
        return f'<TripDestination {self.name}>'


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)  # Add index for searching
    city = db.Column(db.String(120), nullable=True, index=True)  # Add index for searching
    country = db.Column(db.String(120), nullable=True, index=True)  # Add index for searching
    image_url = db.Column(db.String(500), nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON string for categories/tags
    rating = db.Column(db.Float, default=0.0, nullable=False, index=True)  # Add rating for sorting
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)  # Add index for sorting

    user = db.relationship("User", backref=db.backref("wishlist_items", lazy="dynamic", order_by="WishlistItem.created_at.desc()"))

    def __repr__(self):
        return f'<WishlistItem {self.title}>'
    
    @classmethod
    def search_recommendations(cls, user_id=None, query=None, tag=None, limit=None, offset=0, order_by='rating', order_dir='desc'):
        """Fast search for recommendations with caching potential"""
        # Base query
        if user_id:
            base_query = cls.query.filter_by(user_id=user_id)
        else:
            # For global recommendations, use a more complex query
            base_query = cls.query
        
        # Apply text search
        if query:
            search_filter = db.or_(
                cls.title.ilike(f'%{query}%'),
                cls.city.ilike(f'%{query}%'),
                cls.country.ilike(f'%{query}%'),
                cls.tags.ilike(f'%{query}%')
            )
            base_query = base_query.filter(search_filter)
        
        # Apply tag filter
        if tag:
            base_query = base_query.filter(cls.tags.ilike(f'%{tag}%'))
        
        # Apply sorting
        if order_by == 'title':
            order_column = cls.title
        elif order_by == 'created_at':
            order_column = cls.created_at
        elif order_by == 'rating':
            order_column = cls.rating
        else:
            order_column = cls.rating
            
        if order_dir == 'asc':
            base_query = base_query.order_by(order_column.asc())
        else:
            base_query = base_query.order_by(order_column.desc())
        
        # Apply pagination
        if offset:
            base_query = base_query.offset(offset)
        if limit:
            base_query = base_query.limit(limit)
            
        return base_query.all()


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    message = db.Column(db.String(500), nullable=False)
    kind = db.Column(db.String(50), nullable=True, index=True)  # Add index for filtering by type
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Add index for filtering
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)  # Add index for sorting

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic", order_by="Notification.created_at.desc()"))

    def __repr__(self):
        return f'<Notification {self.message[:50]}>'


# Add utility class for fast search algorithms
class SearchUtils:
    """Utility class for implementing fast search algorithms"""
    
    @staticmethod
    def fuzzy_search_score(query, text, threshold=0.6):
        """Calculate fuzzy search score using Levenshtein distance"""
        if not query or not text:
            return 0.0
            
        query = query.lower().strip()
        text = text.lower().strip()
        
        # Exact match gets highest score
        if query == text:
            return 1.0
            
        # Check if query is a substring
        if query in text:
            return 0.8
            
        # Simple character overlap scoring
        query_chars = set(query)
        text_chars = set(text)
        overlap = len(query_chars.intersection(text_chars))
        max_chars = max(len(query_chars), len(text_chars))
        
        if max_chars == 0:
            return 0.0
            
        score = overlap / max_chars
        return score if score >= threshold else 0.0
    
    @staticmethod
    def quick_sort_trips(trips, sort_by='created_at', reverse=False):
        """Fast quicksort implementation for trip sorting"""
        if len(trips) <= 1:
            return trips
            
        def get_sort_key(trip):
            if sort_by == 'title':
                return trip.title.lower() if trip.title else ''
            elif sort_by == 'start_date':
                return trip.start_date if trip.start_date else datetime.min.date()
            elif sort_by == 'status':
                # Define status priority for sorting
                status_priority = {'planned': 1, 'in_progress': 2, 'completed': 3}
                return status_priority.get(trip.status, 0)
            elif sort_by == 'priority':
                return trip.priority if hasattr(trip, 'priority') else 0
            else:  # created_at
                return trip.created_at if trip.created_at else datetime.min
        
        def quicksort(arr):
            if len(arr) <= 1:
                return arr
            
            pivot = arr[len(arr) // 2]
            pivot_key = get_sort_key(pivot)
            
            left = [x for x in arr if get_sort_key(x) < pivot_key]
            middle = [x for x in arr if get_sort_key(x) == pivot_key]
            right = [x for x in arr if get_sort_key(x) > pivot_key]
            
            result = quicksort(left) + middle + quicksort(right)
            return result[::-1] if reverse else result
        
        return quicksort(trips)
    
    @staticmethod
    def binary_search_insert_position(arr, item, key_func):
        """Binary search to find insertion position for maintaining sorted order"""
        left, right = 0, len(arr)
        item_key = key_func(item)
        
        while left < right:
            mid = (left + right) // 2
            if key_func(arr[mid]) < item_key:
                left = mid + 1
            else:
                right = mid
                
        return left
    
    @staticmethod
    def paginate_results(results, page=1, per_page=20):
        """Efficient pagination helper"""
        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            'items': results[start:end],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': end < total
        }


class TripExpense(db.Model):
    __tablename__ = "trip_expenses"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # accommodation, meals, transport, activities, shopping, other
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    expense_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey("trip_destinations.id"), nullable=True, index=True)  # Optional link to specific destination

    trip = db.relationship("Trip", backref=db.backref("expenses", lazy="dynamic"))
    destination = db.relationship("TripDestination", backref=db.backref("expenses", lazy="dynamic"))

    def __repr__(self):
        return f'<TripExpense {self.category}: ₹{self.amount}>'
