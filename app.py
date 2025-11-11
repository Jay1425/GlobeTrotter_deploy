from flask import Flask, render_template, url_for, request, redirect, flash, session, jsonify
from models import db, User, Trip, TripDestination, WishlistItem, Notification, TripExpense
from routes.budget_routes import budget_routes
from routes.cities_routes import cities_routes
from forms import LoginForm, SignupForm
from flask_dance.contrib.google import make_google_blueprint, google
from flask_mail import Mail, Message
import os
import json
import time
import secrets
import hashlib
from datetime import date, datetime, timedelta

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Register blueprints
app.register_blueprint(budget_routes)
app.register_blueprint(cities_routes)

# Production-ready configuration with environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    # Render uses postgres:// but SQLAlchemy requires postgresql://
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Determine if we're in production
IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

app.config.update(
	SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production"),
	SQLALCHEMY_DATABASE_URI=DATABASE_URL or "sqlite:///instance/globetrotter.db",
	SQLALCHEMY_TRACK_MODIFICATIONS=False,
	SQLALCHEMY_ENGINE_OPTIONS={
		"pool_pre_ping": True,  # Verify connections before using
		"pool_recycle": 300,  # Recycle connections after 5 minutes
	} if IS_PRODUCTION else {},
	# Flask-Dance config
	OAUTHLIB_INSECURE_TRANSPORT=not IS_PRODUCTION,  # Only for local dev
	# Session cookie settings
	SESSION_COOKIE_SAMESITE="Lax",
	SESSION_COOKIE_SECURE=IS_PRODUCTION,  # Only use secure cookies in production
	SESSION_COOKIE_HTTPONLY=True,
	SERVER_NAME=None if IS_PRODUCTION else "localhost:5000",  # Don't set SERVER_NAME in production
	# Email configuration
	MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
	MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
	MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true',
	MAIL_USE_SSL=False,
	MAIL_USERNAME=os.environ.get('MAIL_USERNAME', 'aivisionaries.teams@gmail.com'),
	MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD', 'rvesfkcwikpqmbmw'),
	MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'aivisionaries.teams@gmail.com'),
	MAIL_DEBUG=not IS_PRODUCTION,  # Disable debug in production
	MAIL_SUPPRESS_SEND=False,  # Allow sending emails
)
db.init_app(app)

# Initialize Flask-Mail
mail = Mail(app)

def send_otp_email(user, otp_code):
	"""Send OTP verification email to user"""
	try:
		msg = Message(
			subject="Email Verification - GlobeTrotter",
			recipients=[user.email],
			html=f'''
			<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafc;">
				<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
					<h1 style="color: white; margin: 0; font-size: 28px;">Email Verification</h1>
					<p style="color: white; margin: 10px 0 0 0; opacity: 0.9;">GlobeTrotter</p>
				</div>
				
				<div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
					<h2 style="color: #1a202c; margin-top: 0;">Hello {user.first_name}!</h2>
					<p style="color: #4a5568; line-height: 1.6;">Thank you for registering with GlobeTrotter! To complete your email verification, please use the following 6-digit code:</p>
					
					<div style="background: #f7fafc; border: 2px dashed #cbd5e0; border-radius: 8px; padding: 20px; text-align: center; margin: 30px 0;">
						<div style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #3182ce; font-family: monospace;">{otp_code}</div>
					</div>
					
					<p style="color: #4a5568; line-height: 1.6;">This code will expire in <strong>10 minutes</strong>. If you didn't request this verification, please ignore this email.</p>
					
					<div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
						<p style="color: #718096; font-size: 14px; margin: 0;">Best regards,<br>The GlobeTrotter Team</p>
					</div>
				</div>
				
				<div style="text-align: center; margin-top: 20px;">
					<p style="color: #718096; font-size: 12px;">If you have any questions, please contact our support team.</p>
				</div>
			</div>
			'''
		)
		mail.send(msg)
		return True
	except Exception as e:
		print(f"Failed to send OTP email: {e}")
		return False

# Add custom Jinja2 filter for JSON parsing
@app.template_filter('fromjson')
def fromjson_filter(value):
	if not value:
		return []
	try:
		import json
		return json.loads(value)
	except:
		return []

# Helper function for user authentication
def get_current_user():
	"""Get the current logged-in user or redirect to login if not found"""
	if "user_email" not in session:
		return None
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		# User not found, clear session
		session.clear()
		return None
	
	return user

def get_verified_user():
	"""Get the current logged-in and email-verified user"""
	user = get_current_user()
	if user and user.is_email_verified:
		return user
	return None

def require_email_verification(user):
	"""Helper function to redirect unverified users to email verification"""
	if not user.is_email_verified:
		# Generate new OTP and redirect to verification
		otp_code = user.generate_otp()
		db.session.commit()
		
		if send_otp_email(user, otp_code):
			session['verification_email'] = user.email
			session.pop('user_email', None)  # Clear login session
			return redirect(url_for("verify_email"))
		else:
			flash("Failed to send verification email. Please contact support.", "error")
			return redirect(url_for("login"))
	return None

def require_user():
	"""Require a logged-in user, redirect to login if not found"""
	user = get_current_user()
	if not user:
		flash("Please log in to access this page.", "error")
		return redirect(url_for("login"))
	return user

# Context processor to make current_user available in all templates
@app.context_processor
def inject_user():
	"""Make current_user available in all templates"""
	current_user = get_current_user()
	return dict(current_user=current_user)

# Allow HTTP for local dev and relax scope validation to avoid scope-change errors
if not IS_PRODUCTION:
	os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
	os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# Google OAuth setup with environment variables
# Get credentials from environment - NO DEFAULTS for security
google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

if not google_client_id or not google_client_secret:
	print("WARNING: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables not set.")
	print("Google OAuth login will not work until these are configured.")
	# Use dummy values to prevent blueprint creation errors, but OAuth won't work
	google_client_id = google_client_id or 'GOOGLE_CLIENT_ID_NOT_SET'
	google_client_secret = google_client_secret or 'GOOGLE_CLIENT_SECRET_NOT_SET'

google_bp = make_google_blueprint(
	client_id=google_client_id,
	client_secret=google_client_secret,
	# Use Google's recommended OpenID Connect scopes to avoid scope-change warnings
	scope=[
		"openid",
		"https://www.googleapis.com/auth/userinfo.profile",
		"https://www.googleapis.com/auth/userinfo.email",
	],
	# After token exchange, redirect here to finalize login
	redirect_to="google_post_login",
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/google/post-login")
def google_post_login():
	# This is called after Flask-Dance's authorized view completes token exchange
	if not google.authorized:
		flash("Google login failed or was cancelled.", "error")
		return redirect(url_for("login"))
	resp = google.get("/oauth2/v2/userinfo")
	if not resp.ok:
		flash("Failed to fetch user info from Google.", "error")
		return redirect(url_for("login"))
	info = resp.json()
	email = info.get("email")
	first_name = info.get("given_name", "")
	last_name = info.get("family_name", "")
	if not email:
		flash("Google account did not provide an email.", "error")
		return redirect(url_for("login"))
	
	# Check if user already exists (from any registration method)
	user = User.query.filter_by(email=email.lower()).first()
	if not user:
		# Create new user only if email doesn't exist
		try:
			user = User(
				first_name=first_name or "User",
				last_name=last_name or "",
				email=email.lower(),
				phone=None,
				city=None,
				country=None,
			)
			user.set_password("google-oauth")  # Placeholder, not used
			db.session.add(user)
			db.session.commit()
			flash(f"Welcome to GlobeTrotter, {user.first_name}! Account created via Google.", "success")
		except Exception as e:
			db.session.rollback()
			flash("An error occurred while creating your account. Please try again.", "error")
			print(f"Google OAuth signup error: {e}")
			return redirect(url_for("login"))
	else:
		# User exists, just log them in
		flash(f"Welcome back, {user.first_name}! Logged in via Google.", "success")
	
	# If user is not verified, send OTP and redirect to verification page
	if not user.is_email_verified:
		otp_code = user.generate_otp()
		db.session.commit()
		if send_otp_email(user, otp_code):
			session['verification_email'] = user.email
			flash("Please verify your email address. We've sent a verification code to your email.", "warning")
			return redirect(url_for("verify_email"))
		else:
			flash("Failed to send verification email. Please try again.", "error")
			return redirect(url_for("login"))
	# Log in the user (session-based, minimal)
	session["user_email"] = user.email
	return redirect(url_for("dashboard"))


@app.route("/")
def home():
	return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data.strip().lower()).first()
		if user and user.check_password(form.password.data):
			# Check if email is verified
			if not user.is_email_verified:
				# Generate new OTP and send email
				otp_code = user.generate_otp()
				db.session.commit()
				
				if send_otp_email(user, otp_code):
					session['verification_email'] = user.email
					flash("Please verify your email address. We've sent a new verification code to your email.", "warning")
					return redirect(url_for("verify_email"))
				else:
					flash("Failed to send verification email. Please try again later.", "error")
					return render_template("auth/login.html", form=form)
			
			# Email is verified, proceed with login
			flash("Logged in successfully.", "success")
			# set session for logged in user
			session["user_email"] = user.email
			# Update last login
			user.last_login = datetime.utcnow()
			db.session.commit()
			return redirect(url_for("dashboard"))
		flash("Invalid email or password.", "error")
	return render_template("auth/login.html", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
	form = SignupForm()
	if form.validate_on_submit():
		# Prevent duplicate emails
		email = form.email.data.strip().lower()
		existing_user = User.query.filter_by(email=email).first()
		if existing_user:
			flash("This email is already registered. Please use a different email or try logging in.", "error")
		else:
			try:
				user = User(
					first_name=form.first_name.data.strip(),
					last_name=form.last_name.data.strip(),
					email=email,
					phone=form.phone.data.strip() if form.phone.data else None,
					city=form.city.data.strip() if form.city.data else None,
					country=form.country.data if form.country.data else None,
					is_email_verified=False  # Email verification required
				)
				user.set_password(form.password.data)
				
				# Generate and send OTP
				otp_code = user.generate_otp()
				
				db.session.add(user)
				db.session.commit()
				
				# Send OTP email
				if send_otp_email(user, otp_code):
					# Store user email in session for verification process
					session['verification_email'] = user.email
					flash("Account created successfully! Please check your email for the verification code.", "success")
					return redirect(url_for("verify_email"))
				else:
					# If email fails, delete the user and show error
					db.session.delete(user)
					db.session.commit()
					flash("Failed to send verification email. Please try again.", "error")
					
			except Exception as e:
				db.session.rollback()
				flash("An error occurred while creating your account. Please try again.", "error")
				print(f"Signup error: {e}")
	return render_template("auth/signup.html", form=form)


@app.route("/forgot-password", methods=["GET"])
def forgot_password_page():
	"""Render the forgot password page"""
	return render_template("auth/forgot_password.html")


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
	"""Handle forgot password requests"""
	try:
		# Check if this is an AJAX request
		is_ajax = (request.headers.get('Accept', '').find('application/json') != -1 or 
		          request.headers.get('X-Requested-With') == 'XMLHttpRequest')
		
		# Get email from request (support both JSON and form data)
		if request.is_json:
			email = request.json.get('email')
		else:
			email = request.form.get('email') or request.form.get('resetEmail')
		
		if not email:
			if request.is_json or is_ajax:
				return jsonify({"success": False, "message": "Email is required"}), 400
			else:
				flash("Email is required", "error")
				return redirect(url_for('forgot_password_page'))
		
		email = email.strip().lower()
		
		# Check if user exists
		user = User.query.filter_by(email=email).first()
		
		if user:
			# Generate password reset token
			token = user.generate_reset_token()
			db.session.commit()
			
			try:
				# Create reset URL
				reset_url = url_for('reset_password_page', token=token, _external=True)
				
				# Create email message
				msg = Message(
					subject='Password Reset Request - GlobeTrotter',
					recipients=[email],
					html=f'''
					<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
						<div style="text-align: center; margin-bottom: 30px;">
							<h1 style="color: #3B82F6; margin: 0;">GlobeTrotter</h1>
							<p style="color: #64748B; margin: 5px 0;">Password Reset Request</p>
						</div>
						
						<div style="background: #F0F4F8; padding: 30px; border-radius: 10px; margin-bottom: 20px;">
							<h2 style="color: #1A2B3D; margin-top: 0;">Hello {user.first_name},</h2>
							<p style="color: #64748B; line-height: 1.6;">
								We received a request to reset your password for your GlobeTrotter account. 
								Click the button below to create a new password:
							</p>
							
							<div style="text-align: center; margin: 30px 0;">
								<a href="{reset_url}" 
								   style="background: linear-gradient(to right, #3B82F6, #2563EB); 
								          color: white; padding: 15px 30px; text-decoration: none; 
								          border-radius: 8px; font-weight: bold; display: inline-block;">
									Reset Your Password
								</a>
							</div>
							
							<p style="color: #64748B; font-size: 14px; line-height: 1.6;">
								This link will expire in 1 hour for security reasons. If you didn't request this 
								password reset, please ignore this email or contact our support team.
							</p>
						</div>
						
						<div style="text-align: center; color: #64748B; font-size: 12px;">
							<p>If the button doesn't work, copy and paste this link into your browser:</p>
							<p style="word-break: break-all; color: #3B82F6;">{reset_url}</p>
						</div>
					</div>
					'''
				)
				
				# Try to send email
				mail.send(msg)
				
				message = f"Password reset link sent to {email}. Please check your email and follow the instructions."
				if request.is_json or is_ajax:
					return jsonify({"success": True, "message": message}), 200
				else:
					flash(message, "success")
					return redirect(url_for('forgot_password_page'))
					
			except Exception as email_error:
				print(f"Email sending error: {email_error}")
				print(f"Email error details: {type(email_error).__name__}: {str(email_error)}")
				
				# Fallback: Provide the reset link directly when email fails
				reset_url = url_for('reset_password_page', token=token, _external=True)
				
				message = f"""Email service is temporarily unavailable. You can reset your password directly using this link: 
				<br><br><a href="{reset_url}" class="text-blue-600 hover:underline">{reset_url}</a>
				<br><br><small class="text-gray-600">This link expires in 1 hour.</small>"""
				
				if request.is_json or is_ajax:
					return jsonify({
						"success": True, 
						"message": "Email service unavailable. Check the reset link provided.",
						"reset_url": reset_url
					}), 200
				else:
					flash(message, "warning")
					return redirect(url_for('forgot_password_page'))
		else:
			# For security, don't reveal if email exists or not
			message = "If the email exists in our system, you will receive a password reset link."
			if request.is_json or is_ajax:
				return jsonify({"success": True, "message": message}), 200
			else:
				flash(message, "info")
				return redirect(url_for('forgot_password_page'))
			
	except Exception as e:
		print(f"Forgot password error: {e}")
		error_message = "An error occurred. Please try again."
		if request.is_json or is_ajax:
			return jsonify({"success": False, "message": error_message}), 500
		else:
			flash(error_message, "error")
			return redirect(url_for('forgot_password_page'))
			flash(error_message, "error")
			return redirect(url_for('forgot_password_page'))


@app.route("/reset-password/<token>", methods=["GET"])
def reset_password_page(token):
	"""Render password reset page with token validation"""
	# Verify token exists and is not expired
	user = User.query.filter_by(reset_token=token).first()
	
	if not user or not user.verify_reset_token(token):
		flash("Invalid or expired password reset link. Please request a new one.", "error")
		return redirect(url_for('forgot_password_page'))
	
	return render_template("auth/reset_password.html", token=token)


@app.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
	"""Handle password reset form submission"""
	try:
		# Verify token
		user = User.query.filter_by(reset_token=token).first()
		
		if not user or not user.verify_reset_token(token):
			flash("Invalid or expired password reset link. Please request a new one.", "error")
			return redirect(url_for('forgot_password_page'))
		
		# Get new password from form
		new_password = request.form.get('password')
		confirm_password = request.form.get('confirm_password')
		
		if not new_password or not confirm_password:
			flash("Please fill in all fields.", "error")
			return redirect(url_for('reset_password_page', token=token))
		
		if new_password != confirm_password:
			flash("Passwords do not match.", "error")
			return redirect(url_for('reset_password_page', token=token))
		
		if len(new_password) < 6:
			flash("Password must be at least 6 characters long.", "error")
			return redirect(url_for('reset_password_page', token=token))
		
		# Update password and clear reset token
		user.set_password(new_password)
		user.clear_reset_token()
		db.session.commit()
		
		flash("Your password has been successfully reset. You can now log in with your new password.", "success")
		return redirect(url_for('login'))
		
	except Exception as e:
		print(f"Password reset error: {e}")
		flash("An error occurred while resetting your password. Please try again.", "error")
		return redirect(url_for('reset_password_page', token=token))


# Debug route to view reset tokens (for development/testing only)
@app.route("/debug/reset-tokens")
def debug_reset_tokens():
	if not session.get("user_email"):
		return "Please log in first"
	
	users_with_tokens = User.query.filter(User.reset_token.isnot(None)).all()
	
	debug_info = "<h3>Active Reset Tokens (Development Only)</h3><br>"
	
	if not users_with_tokens:
		debug_info += "<p>No active reset tokens found.</p>"
	else:
		for user in users_with_tokens:
			reset_url = url_for('reset_password_page', token=user.reset_token, _external=True)
			expiry_status = "EXPIRED" if user.reset_token_expiry < datetime.utcnow() else "VALID"
			
			debug_info += f"""
			<div style="border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px;">
				<strong>User:</strong> {user.email} ({user.first_name})<br>
				<strong>Token Status:</strong> {expiry_status}<br>
				<strong>Expires:</strong> {user.reset_token_expiry}<br>
				<strong>Reset Link:</strong> <a href="{reset_url}">{reset_url}</a>
			</div>
			"""
	
	debug_info += '<br><a href="/forgot-password">← Back to Forgot Password</a>'
	return debug_info


# Email Verification Routes
@app.route("/verify-email", methods=["GET", "POST"])
def verify_email():
	# Check if user has verification email in session
	if 'verification_email' not in session:
		flash("Please sign up or log in first.", "error")
		return redirect(url_for('login'))
	
	email = session['verification_email']
	user = User.query.filter_by(email=email).first()
	
	if not user:
		session.pop('verification_email', None)
		flash("User not found. Please sign up again.", "error")
		return redirect(url_for('signup'))
	
	if user.is_email_verified:
		session.pop('verification_email', None)
		flash("Email already verified. You can now log in.", "success")
		return redirect(url_for('login'))
	
	if request.method == "POST":
		otp_code = request.form.get('otp_code', '').strip()
		
		if not otp_code or len(otp_code) != 6:
			flash("Please enter a valid 6-digit verification code.", "error")
			return render_template("auth/verify_email.html", email=email)
		
		if user.verify_otp(otp_code):
			# OTP is valid, verify the user
			user.is_email_verified = True
			user.clear_otp()
			db.session.commit()
			
			# Clear verification session
			session.pop('verification_email', None)
			
			# Log the user in
			session["user_email"] = user.email
			user.last_login = datetime.utcnow()
			db.session.commit()
			
			flash("Email verified successfully! Welcome to GlobeTrotter!", "success")
			return redirect(url_for("dashboard"))
		else:
			flash("Invalid or expired verification code. Please try again.", "error")
	
	return render_template("auth/verify_email.html", email=email)


@app.route("/verify-email/resend", methods=["POST"])
def resend_verification_code():
	# Check if user has verification email in session
	if 'verification_email' not in session:
		return jsonify({"error": "No verification session found"}), 400
	
	email = session['verification_email']
	user = User.query.filter_by(email=email).first()
	
	if not user:
		return jsonify({"error": "User not found"}), 404
	
	if user.is_email_verified:
		return jsonify({"error": "Email already verified"}), 400
	
	# Generate new OTP
	otp_code = user.generate_otp()
	db.session.commit()
	
	# Send new OTP email
	if send_otp_email(user, otp_code):
		return jsonify({"success": True, "message": "New verification code sent"}), 200
	else:
		return jsonify({"error": "Failed to send verification code"}), 500


# Explore main landing
@app.route("/explore")
def explore_home():
	return render_template("trip/activity_search.html")

# Trip: Activity Search page
@app.route("/trip/activity-search")
@app.route("/trip/<int:trip_id>/activity-search")
@app.route("/trip/<int:trip_id>/activity-search/<int:section_id>")
def trip_activity_search(trip_id=None, section_id=None):
	# Get current user for authentication
	user = get_current_user()
	if not user:
		flash("Please log in to access this page.", "error")
		return redirect(url_for("login"))
	
	# If trip_id is provided, get trip details
	trip = None
	if trip_id:
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			flash("Trip not found.", "error")
			return redirect(url_for("my_trips"))
	
	# Pass context to template
	context = {
		'trip': trip,
		'trip_id': trip_id,
		'section_id': section_id,
		'return_url': f'/itinerary/{trip_id}' if trip_id else '/dashboard'
	}
	
	return render_template("trip/activity_search.html", **context)

# Additional trip utility pages
@app.route("/trip/city-search")
def trip_city_search():
    return render_template("trip/city_search.html")

@app.route("/trip/<int:trip_id>/view")
def trip_view(trip_id):
    """View the complete itinerary in timeline or calendar format"""
    if not session.get("user_email"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    user = User.query.filter_by(email=session["user_email"]).first()
    trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
    
    if not trip:
        flash("Trip not found.", "error")
        return redirect(url_for("my_trips"))

    # Parse and format destination data
    formatted_destinations = []
    for dest in trip.destinations:
        try:
            # Parse date range if available
            date_range = None
            if ' to ' in (dest.date_range or ''):
                start_str, end_str = dest.date_range.split(' to ')
                start_date = datetime.strptime(start_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_str, '%Y-%m-%d')
                date_range = {
                    'start': start_date,
                    'end': end_date,
                    'duration': (end_date - start_date).days + 1
                }

            # Format activities with suggested timings
            suggested_timings = [
                '09:00 AM', '10:30 AM', '12:00 PM', '02:00 PM', 
                '03:30 PM', '05:00 PM', '06:30 PM', '08:00 PM'
            ]
            
            activities = []
            for idx, activity in enumerate(dest.activities or []):
                activity_data = {
                    'name': activity.name if hasattr(activity, 'name') else str(activity),
                    'time': suggested_timings[idx % len(suggested_timings)],
                    'duration': '1.5 hours',  # Default duration
                    'category': activity.category if hasattr(activity, 'category') else 'Sightseeing',
                    'cost': activity.cost if hasattr(activity, 'cost') else None,
                    'status': 'planned'
                }
                activities.append(activity_data)

            formatted_dest = {
                'name': dest.name,
                'city': dest.city,
                'country': dest.country or 'India',
                'date_range': date_range,
                'budget': dest.budget or 0,
                'activities': activities,
                'coordinates': dest.coordinates if hasattr(dest, 'coordinates') else None,
                'sequence': dest.sequence or (dest.order_index + 1)
            }
            formatted_destinations.append(formatted_dest)
        except Exception as e:
            print(f"Error formatting destination: {e}")
            continue

    # Generate calendar data for the entire trip duration
    calendar_days = []
    if trip.start_date and trip.end_date:
        from datetime import datetime, timedelta
        current_date = trip.start_date
        while current_date <= trip.end_date:
            day_activities = []
            for dest in formatted_destinations:
                if dest.get('date_range'):
                    if dest['date_range']['start'].date() <= current_date <= dest['date_range']['end'].date():
                        day_activities.extend(dest['activities'])
            
            calendar_days.append({
                'date': current_date,
                'activities': day_activities,
                'destination': next((d for d in formatted_destinations 
                                   if d.get('date_range') and 
                                   d['date_range']['start'].date() <= current_date <= d['date_range']['end'].date()), None)
            })
            current_date += timedelta(days=1)

    # Get weather data for first destination
    weather_data = None
    if formatted_destinations and formatted_destinations[0].get('coordinates'):
        coords = formatted_destinations[0]['coordinates']
        try:
            import requests
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lng']}&appid=3422434e8bc000623c0f52a0b92c64ac&units=metric"
            response = requests.get(weather_url)
            if response.ok:
                weather_data = response.json()
        except Exception as e:
            print(f"Error fetching weather: {e}")
    
    return render_template("trip/itinerary_view.html", 
                         trip=trip,
                         destinations=formatted_destinations,
                         calendar_days=calendar_days,
                         weather=weather_data,
                         today=datetime.now().date())
@app.route("/api/city-data")
def get_city_data():
    """Get detailed city information for search results"""
    city_name = request.args.get('city', '').strip()
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    
    if not city_name:
        return jsonify({"error": "City name is required"}), 400
    
    # Indian cities database with comprehensive information
    indian_cities_db = {
        'jaipur': {
            'id': 'jaipur',
            'name': 'Jaipur',
            'state': 'Rajasthan',
            'country': 'India',
            'costIndex': 'medium',
            'popularity': 'high',
            'bestTime': 'Oct-Mar',
            'avgCost': 3500,
            'weatherScore': 4.0,
            'cultureScore': 4.8,
            'highlights': ['Pink City', 'Amber Fort', 'City Palace', 'Hawa Mahal'],
            'description': 'The Pink City of India, known for its stunning Rajput architecture and vibrant culture.',
            'imageUrl': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&h=500&fit=crop'
        },
        'goa': {
            'id': 'goa',
            'name': 'Goa',
            'state': 'Goa',
            'country': 'India',
            'costIndex': 'medium',
            'popularity': 'high',
            'bestTime': 'Nov-Feb',
            'avgCost': 4000,
            'weatherScore': 4.3,
            'cultureScore': 4.2,
            'highlights': ['Beaches', 'Portuguese Architecture', 'Nightlife', 'Water Sports'],
            'description': 'India\'s premier beach destination with Portuguese heritage and vibrant nightlife.',
            'imageUrl': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&h=500&fit=crop'
        },
        'kochi': {
            'id': 'kochi',
            'name': 'Kochi',
            'state': 'Kerala',
            'country': 'India',
            'costIndex': 'low',
            'popularity': 'medium',
            'bestTime': 'Oct-Mar',
            'avgCost': 2800,
            'weatherScore': 3.8,
            'cultureScore': 4.5,
            'highlights': ['Backwaters', 'Spice Markets', 'Chinese Fishing Nets', 'Fort Kochi'],
            'description': 'The Queen of Arabian Sea, famous for backwaters and spice trade history.',
            'imageUrl': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&h=500&fit=crop'
        },
        'udaipur': {
            'id': 'udaipur',
            'name': 'Udaipur',
            'state': 'Rajasthan',
            'country': 'India',
            'costIndex': 'medium',
            'popularity': 'high',
            'bestTime': 'Oct-Mar',
            'avgCost': 3800,
            'weatherScore': 4.1,
            'cultureScore': 4.9,
            'highlights': ['City of Lakes', 'Lake Palace', 'Rajput Architecture', 'City Palace'],
            'description': 'The Venice of the East, renowned for its lakes and magnificent palaces.',
            'imageUrl': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=500&fit=crop'
        },
        'varanasi': {
            'id': 'varanasi',
            'name': 'Varanasi',
            'state': 'Uttar Pradesh',
            'country': 'India',
            'costIndex': 'low',
            'popularity': 'medium',
            'bestTime': 'Oct-Mar',
            'avgCost': 2200,
            'weatherScore': 3.5,
            'cultureScore': 5.0,
            'highlights': ['Spiritual Capital', 'Ganges Ghats', 'Ancient Temples', 'Ganga Aarti'],
            'description': 'One of the world\'s oldest cities and the spiritual capital of India.',
            'imageUrl': 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=800&h=500&fit=crop'
        },
        'agra': {
            'id': 'agra',
            'name': 'Agra',
            'state': 'Uttar Pradesh',
            'country': 'India',
            'costIndex': 'low',
            'popularity': 'high',
            'bestTime': 'Oct-Mar',
            'avgCost': 2500,
            'weatherScore': 3.7,
            'cultureScore': 4.8,
            'highlights': ['Taj Mahal', 'Agra Fort', 'Mughal Architecture', 'Mehtab Bagh'],
            'description': 'Home to the iconic Taj Mahal and showcase of Mughal architectural grandeur.',
            'imageUrl': 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&h=500&fit=crop'
        },
        'mumbai': {
            'id': 'mumbai',
            'name': 'Mumbai',
            'state': 'Maharashtra',
            'country': 'India',
            'costIndex': 'high',
            'popularity': 'high',
            'bestTime': 'Nov-Feb',
            'avgCost': 5500,
            'weatherScore': 3.6,
            'cultureScore': 4.4,
            'highlights': ['Bollywood', 'Gateway of India', 'Marine Drive', 'Street Food'],
            'description': 'The financial capital and entertainment hub of India.',
            'imageUrl': 'https://images.unsplash.com/photo-1595658658481-d53d3f999875?w=800&h=500&fit=crop'
        },
        'delhi': {
            'id': 'delhi',
            'name': 'Delhi',
            'state': 'Delhi',
            'country': 'India',
            'costIndex': 'medium',
            'popularity': 'high',
            'bestTime': 'Oct-Mar',
            'avgCost': 4200,
            'weatherScore': 3.4,
            'cultureScore': 4.7,
            'highlights': ['Red Fort', 'India Gate', 'Lotus Temple', 'Chandni Chowk'],
            'description': 'The capital city showcasing India\'s rich history and modern development.',
            'imageUrl': 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&h=500&fit=crop'
        }
    }
    
    # Search for city in database
    city_key = city_name.lower().replace(' ', '')
    city_data = indian_cities_db.get(city_key)
    
    if not city_data:
        # Try partial matching
        for key, data in indian_cities_db.items():
            if city_name.lower() in data['name'].lower() or data['name'].lower() in city_name.lower():
                city_data = data
                break
    
    if not city_data:
        # Return generic data for unknown cities
        city_data = {
            'id': city_key,
            'name': city_name,
            'state': 'Unknown',
            'country': 'India',
            'costIndex': 'medium',
            'popularity': 'medium',
            'bestTime': 'Oct-Mar',
            'avgCost': 3000,
            'weatherScore': 3.5,
            'cultureScore': 4.0,
            'highlights': ['Local Culture', 'Historical Sites', 'Local Cuisine'],
            'description': f'Discover the charm and beauty of {city_name}.',
            'imageUrl': f'https://source.unsplash.com/800x500/?{city_name.replace(" ", "%20")}'
        }
    
    # Add weather data if coordinates provided
    if lat and lng:
        try:
            import requests
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid=3422434e8bc000623c0f52a0b92c64ac&units=metric"
            response = requests.get(weather_url)
            if response.ok:
                weather_data = response.json()
                city_data['weather'] = {
                    'temp': weather_data['main']['temp'],
                    'description': weather_data['weather'][0]['description'],
                    'humidity': weather_data['main']['humidity']
                }
        except Exception as e:
            print(f"Weather API error: {e}")
    
    return jsonify(city_data)

@app.route("/api/cities/search")
def search_cities():
    """Search cities with filters"""
    query = request.args.get('q', '').strip().lower()
    cost_filter = request.args.get('cost', '')
    popularity_filter = request.args.get('popularity', '')
    region = request.args.get('region', '')
    
    # Indian cities database
    indian_cities_db = {
        'jaipur': {
            'id': 'jaipur',
            'name': 'Jaipur',
            'state': 'Rajasthan',
            'country': 'India',
            'costIndex': 'medium',
            'popularity': 'high',
            'bestTime': 'Oct-Mar',
            'avgCost': 3500,
            'weatherScore': 4.0,
            'cultureScore': 4.8,
            'highlights': ['Pink City', 'Amber Fort', 'City Palace', 'Hawa Mahal'],
            'description': 'The Pink City of India, known for its stunning Rajput architecture and vibrant culture.',
            'imageUrl': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&h=500&fit=crop'
        },
        'goa': {
            'id': 'goa',
            'name': 'Goa',
            'state': 'Goa',
            'country': 'India',
            'costIndex': 'medium',
            'popularity': 'high',
            'bestTime': 'Nov-Feb',
            'avgCost': 4000,
            'weatherScore': 4.3,
            'cultureScore': 4.2,
            'highlights': ['Beaches', 'Portuguese Architecture', 'Nightlife', 'Water Sports'],
            'description': 'India\'s premier beach destination with Portuguese heritage and vibrant nightlife.',
            'imageUrl': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&h=500&fit=crop'
        },
        'kochi': {
            'id': 'kochi',
            'name': 'Kochi',
            'state': 'Kerala',
            'country': 'India',
            'costIndex': 'low',
            'popularity': 'medium',
            'bestTime': 'Oct-Mar',
            'avgCost': 2800,
            'weatherScore': 3.8,
            'cultureScore': 4.5,
            'highlights': ['Backwaters', 'Spice Markets', 'Chinese Fishing Nets', 'Fort Kochi'],
            'description': 'The Queen of Arabian Sea, famous for backwaters and spice trade history.',
            'imageUrl': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&h=500&fit=crop'
        }
    }
    
    # Apply filters
    filtered_cities = []
    for city_id, city_data in indian_cities_db.items():
        # Text search
        if query and query not in city_data['name'].lower() and query not in city_data['state'].lower():
            continue
            
        # Cost filter
        if cost_filter and city_data['costIndex'] != cost_filter:
            continue
            
        # Popularity filter
        if popularity_filter and city_data['popularity'] != popularity_filter:
            continue
            
        filtered_cities.append(city_data)
    
    return jsonify({
        'cities': filtered_cities,
        'total': len(filtered_cities)
    })

@app.route("/trip/budget")
def trip_budget_breakdown():
    return render_template("trip/budget_breakdown.html")
@app.route("/trip/calendar")
def trip_calendar():
	if not session.get("user_email"):
		flash("Please log in to access this page.", "error")
		return redirect(url_for("login"))
	return render_template("trip/trip_calendar.html")

@app.route("/trip/<int:trip_id>/calendar")
def trip_calendar_view(trip_id):
	"""Calendar view for a specific trip"""
	if not session.get("user_email"):
		flash("Please log in to access this page.", "error")
		return redirect(url_for("login"))
	
	user = User.query.filter_by(email=session["user_email"]).first()
	trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
	
	if not trip:
		flash("Trip not found.", "error")
		return redirect(url_for("my_trips"))
	
	return render_template("trip/trip_calendar.html", trip=trip)


@app.route("/trip/public")
@app.route("/trip/public/<int:trip_id>")
def public_itinerary(trip_id: int | None = None):
	# For now, render a public itinerary shell; could be extended to fetch by trip_id
	return render_template("trip/public_itinerary.html")

@app.route("/dashboard")
def dashboard():
	if not session.get("user_email"):
		flash("Please log in to access your dashboard.", "error")
		return redirect(url_for("login"))
	
	user = get_current_user()
	if not user:
		flash("User not found. Please log in again.", "error")
		return redirect(url_for("login"))
	
	# Check if email verification is required
	verification_redirect = require_email_verification(user)
	if verification_redirect:
		return verification_redirect
	
	# User is verified, proceed with dashboard
	# Enhanced statistics for dashboard
	trips_q = Trip.query.filter_by(user_id=user.id)
	total_trips = trips_q.count()
	completed_trips = trips_q.filter(Trip.status == "completed").count()
	upcoming_trips = trips_q.filter(Trip.start_date != None, Trip.start_date >= date.today()).count()
	
	# Places visited from trip destinations
	dest_rows = (
		db.session.query(TripDestination.name, TripDestination.city, TripDestination.country)
		.join(Trip, Trip.id == TripDestination.trip_id)
		.filter(Trip.user_id == user.id)
		.all()
	)
	places_visited = len(list({(n or "", c or "", co or "") for (n, c, co) in dest_rows}))
	
	# Budget calculations
	total_budget = db.session.query(db.func.sum(Trip.budget)).filter_by(user_id=user.id).scalar() or 0
	avg_budget = total_budget / max(total_trips, 1)
	
	# Recent trips (last 3 for dashboard)
	recent_trips = (
		Trip.query.filter_by(user_id=user.id)
		.order_by(Trip.created_at.desc())
		.limit(3)
		.all()
	)
	
	# Upcoming trips with dates
	next_trip = (
		Trip.query.filter_by(user_id=user.id)
		.filter(Trip.start_date != None, Trip.start_date >= date.today())
		.order_by(Trip.start_date.asc())
		.first()
	)
	
	# Popular destinations from wishlist
	recommended_destinations = (
		WishlistItem.query.filter_by(user_id=user.id)
		.order_by(WishlistItem.rating.desc(), WishlistItem.created_at.desc())
		.limit(6)
		.all()
	)
	
	# If no wishlist items, use recent destinations as recommendations
	if not recommended_destinations:
		recent_destinations = (
			db.session.query(TripDestination)
			.join(Trip, Trip.id == TripDestination.trip_id)
			.filter(Trip.user_id == user.id)
			.order_by(Trip.created_at.desc())
			.limit(6)
			.all()
		)
		recommended_destinations = recent_destinations

	# Enhanced stats for the dashboard
	stats = {
		"total_trips": total_trips,
		"completed_trips": completed_trips,
		"upcoming_trips": upcoming_trips,
		"places_visited": places_visited,
		"total_budget": total_budget,
		"avg_budget": avg_budget,
	}

	return render_template(
		"dashboard.html",
		stats=stats,
		recent_trips=recent_trips,
		next_trip=next_trip,
		recommended_destinations=recommended_destinations,
		user=user,
	)

# API Endpoints for Live Dashboard Data
@app.route('/api/dashboard/stats')
def dashboard_stats_api():
	"""API endpoint for live dashboard statistics"""
	if not session.get("user_email"):
		return jsonify({"error": "Unauthorized"}), 401
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		return jsonify({"error": "User not found"}), 404
	
	# Calculate live stats
	trips_q = Trip.query.filter_by(user_id=user.id)
	total_trips = trips_q.count()
	completed_trips = trips_q.filter(Trip.status == "completed").count()
	upcoming_trips = trips_q.filter(Trip.start_date != None, Trip.start_date >= date.today()).count()
	
	# Places visited calculation
	dest_rows = (
		db.session.query(TripDestination.name, TripDestination.city, TripDestination.country)
		.join(Trip, Trip.id == TripDestination.trip_id)
		.filter(Trip.user_id == user.id)
		.all()
	)
	places_visited = len(list({(n or "", c or "", co or "") for (n, c, co) in dest_rows}))
	
	# Budget calculations
	total_budget = db.session.query(db.func.sum(Trip.budget)).filter_by(user_id=user.id).scalar() or 0
	avg_budget = total_budget / max(total_trips, 1)
	
	return jsonify({
		"stats": {
			"total_trips": total_trips,
			"completed_trips": completed_trips,
			"upcoming_trips": upcoming_trips,
			"places_visited": places_visited,
			"total_budget": float(total_budget),
			"avg_budget": float(avg_budget)
		}
	})

@app.route('/api/dashboard/recent-trips')
def dashboard_recent_trips_api():
	"""API endpoint for recent trips"""
	if not session.get("user_email"):
		return jsonify({"error": "Unauthorized"}), 401
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		return jsonify({"error": "User not found"}), 404
	
	limit = request.args.get('limit', 3, type=int)
	recent_trips = (
		Trip.query.filter_by(user_id=user.id)
		.order_by(Trip.created_at.desc())
		.limit(limit)
		.all()
	)
	
	trips_data = []
	for trip in recent_trips:
		trips_data.append({
			"id": trip.id,
			"title": trip.title,
			"start_date": trip.start_date.isoformat() if trip.start_date else None,
			"end_date": trip.end_date.isoformat() if trip.end_date else None,
			"status": trip.status,
			"budget": float(trip.budget) if trip.budget else 0
		})
	
	return jsonify({"trips": trips_data})

@app.route("/dashboard/create-trip", methods=["GET", "POST"])
def create_trip():
	if not session.get("user_email"):
		flash("Please log in to access this page.", "error")
		return redirect(url_for("login"))
	user = User.query.filter_by(email=session["user_email"]).first()
	if request.method == "POST":
		title = (request.form.get("tripName") or "").strip()
		start_date = request.form.get("startDate") or None
		end_date = request.form.get("endDate") or None
		destination = (request.form.get("destination") or "").strip()
		# Support multi-select destinations from enhanced JS form
		destinations_multi = [d.strip() for d in request.form.getlist("destinations[]") if (d or "").strip()]
		# Basic validation
		if not title:
			flash("Trip name is required.", "error")
			return redirect(url_for("create_trip"))
		try:
			from datetime import datetime
			sd = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
			ed = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
		except Exception:
			sd, ed = None, None
		trip = Trip(user_id=user.id, title=title, start_date=sd, end_date=ed, status="planned")
		db.session.add(trip)
		db.session.flush()  # get trip.id before commit
		# Build destinations list preference: multi-select first, else single field
		ordered_dests = destinations_multi if destinations_multi else ([destination] if destination else [])
		for idx, dest_name in enumerate(ordered_dests):
			if not dest_name:
				continue
			# Store as itinerary entries (names only for now)
			db.session.add(TripDestination(trip_id=trip.id, name=dest_name, order_index=idx, sequence=idx+1))
		db.session.commit()
		flash("Trip created.", "success")
		return redirect(url_for("itinerary", trip_id=trip.id))
	return render_template("dashboard/create_trip.html")

@app.route("/dashboard/my-trips")
def my_trips():
	user = require_user()
	if not isinstance(user, User):  # It's a redirect response
		return user
	
	today = date.today()
	trips_all = Trip.query.filter_by(user_id=user.id).order_by(Trip.created_at.desc()).all()
	trips_ongoing = [t for t in trips_all if t.status in ("in_progress", "ongoing") or (t.start_date and t.end_date and t.start_date <= today <= t.end_date)]
	trips_upcoming = [t for t in trips_all if (t.start_date and t.start_date > today) and t.status not in ("completed",)]
	trips_completed = [t for t in trips_all if t.status == "completed" or (t.end_date and t.end_date < today)]
	# Stats
	ongoing_count = len(trips_ongoing)
	upcoming_count = len(trips_upcoming)
	completed_count = len(trips_completed)
	# Places visited = distinct TripDestination across user's trips
	place_rows = (
		db.session.query(TripDestination.name)
		.join(Trip, Trip.id == TripDestination.trip_id)
		.filter(Trip.user_id == user.id)
		.all()
	)
	places_visited_count = len({(n[0] or "").strip().lower() for n in place_rows})
	return render_template(
		"dashboard/my_trips.html",
		trips_ongoing=trips_ongoing,
		trips_upcoming=trips_upcoming,
		trips_completed=trips_completed,
		today=today,
		stats={
			"ongoing": ongoing_count,
			"upcoming": upcoming_count,
			"completed": completed_count,
			"places": places_visited_count,
		},
	)


@app.context_processor
def inject_current_user():
	email = session.get("user_email")
	user = None
	if email:
		user = User.query.filter_by(email=email).first()
	# Provide unread notifications count globally where possible
	unread_count = 0
	if user:
		try:
			unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
		except Exception as e:
			print(f"Warning: Could not fetch notification count: {e}")
			unread_count = 0
	return {"current_user": user, "unread_count": unread_count}


@app.route("/logout")
def logout():
	# Remove app session info
	session.pop("user_email", None)
	# Remove Google OAuth token if present
	session.pop("google_oauth_token", None)
	flash("You have been logged out.", "success")
	return redirect(url_for("home"))

@app.route("/make-trip")
def make_trip():
	return render_template("dashboard/create_trip.html")

@app.route("/itinerary/<int:trip_id>")
def itinerary(trip_id: int):
	user = require_user()
	if not isinstance(user, User):  # It's a redirect response
		return user
	
	trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
	if not trip:
		flash("Trip not found.", "error")
		return redirect(url_for("my_trips"))
	# Itinerary sections are TripDestination entries ordered by order_index then id
	sections = (
		TripDestination.query.filter_by(trip_id=trip.id)
		.order_by(TripDestination.order_index.asc(), TripDestination.id.asc())
		.all()
	)
	print(f"DEBUG - Found {len(sections)} sections for trip {trip_id}")
	for s in sections:
		print(f"DEBUG - Section: {s.name}, city: {s.city}, date_range: {s.date_range}")
	return render_template("trip/itinerary_builder.html", trip=trip, sections=sections)


@app.route("/api/trips/<int:trip_id>/itinerary", methods=["POST"])
def save_itinerary(trip_id: int):
    """Save itinerary sections with proper data structure and ordering"""
    if not session.get("user_email"):
        return {"ok": False, "error": "auth"}, 401
    
    user = User.query.filter_by(email=session["user_email"]).first()
    trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
    if not trip:
        return {"ok": False, "error": "not_found"}, 404
    
    data = request.get_json(silent=True) or {}
    sections = data.get("sections", [])
    total_budget = data.get("totalBudget", 0)
    
    print(f"DEBUG - Save itinerary called for trip {trip_id}")
    print(f"DEBUG - Received sections: {sections}")
    print(f"DEBUG - Total budget: {total_budget}")
    
    try:
        # Clear existing destinations to prevent duplicates
        TripDestination.query.filter_by(trip_id=trip.id).delete()
        
        # Add new sections with proper ordering
        for section_data in sections:
            if not isinstance(section_data, dict):
                continue
            
            # Handle city data - could be string or object
            city_data = section_data.get("city", "")
            if isinstance(city_data, dict):
                city_name = city_data.get("name", "").strip()
                city_place_id = city_data.get("placeId", "")
            else:
                city_name = str(city_data).strip()
                city_place_id = ""
            
            if not city_name:
                continue
            
            # Get and validate budget
            section_budget = section_data.get("budget", 0)
            try:
                section_budget = float(section_budget) if section_budget else 0
                if section_budget < 0:
                    section_budget = 0  # Prevent negative budgets
            except (ValueError, TypeError):
                section_budget = 0
            
            destination = TripDestination(
                trip_id=trip.id,
                name=city_name,
                city=city_name,  # Store city name in city field too
                order_index=section_data.get("order", 1) - 1,  # 0-based index
                sequence=section_data.get("order", 1),  # 1-based sequence
                date_range=section_data.get("dateRange", ""),
                budget=section_budget,
                notes=json.dumps(section_data.get("activities", []))
            )
            db.session.add(destination)
        
        # Update trip budget if provided (validate non-negative)
        try:
            total_budget = float(total_budget) if total_budget else 0
            if total_budget < 0:
                total_budget = 0  # Prevent negative total budget
        except (ValueError, TypeError):
            total_budget = 0
            
        if total_budget > 0:
            trip.budget = total_budget
        
        db.session.commit()
        return {"ok": True, "count": len(sections), "totalBudget": total_budget}
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving itinerary: {e}")
        return {"ok": False, "error": str(e)}, 500

@app.route("/user/profile-settings")
def profile_settings():
	if not session.get("user_email"):
		flash("Please log in to access this page.", "error")
		return redirect(url_for("login"))
	user = User.query.filter_by(email=session["user_email"]).first()
	# Build stats and trip groupings for the profile page
	today = date.today()
	trips_all = Trip.query.filter_by(user_id=user.id).order_by(Trip.created_at.desc()).all()
	trips_ongoing = [t for t in trips_all if t.status in ("in_progress", "ongoing") or (t.start_date and t.end_date and t.start_date <= today <= t.end_date)]
	trips_upcoming = [t for t in trips_all if (t.start_date and t.start_date > today) and t.status not in ("completed",)]
	trips_completed = [t for t in trips_all if t.status == "completed" or (t.end_date and t.end_date < today)]
	# Places visited = distinct TripDestination across user's trips
	place_rows = (
		db.session.query(TripDestination.name)
		.join(Trip, Trip.id == TripDestination.trip_id)
		.filter(Trip.user_id == user.id)
		.all()
	)
	places_visited_count = len({(n[0] or "").strip().lower() for n in place_rows})
	stats = {
		"trips_completed": len(trips_completed),
		"places": places_visited_count,
		"upcoming": len(trips_upcoming),
		"ongoing": len(trips_ongoing),
	}
	return render_template(
		"user/profile_settings.html",
		stats=stats,
		trips_upcoming=trips_upcoming,
		trips_completed=trips_completed,
		today=today,
	)


# --- Notifications APIs ---
@app.route("/api/notifications", methods=["GET"])
def api_notifications():
	if not session.get("user_email"):
		return {"ok": False, "error": "auth"}, 401
	user = User.query.filter_by(email=session["user_email"]).first()
	items = (
		Notification.query.filter_by(user_id=user.id)
		.order_by(Notification.created_at.desc())
		.limit(20)
		.all()
	)
	return {
		"ok": True,
		"items": [
			{
				"id": n.id,
				"message": n.message,
				"kind": n.kind,
				"is_read": n.is_read,
				"created_at": n.created_at.isoformat(),
			}
			for n in items
		],
	}


@app.route("/api/notifications/mark-read", methods=["POST"])
def api_notifications_mark_read():
	if not session.get("user_email"):
		return {"ok": False, "error": "auth"}, 401
	user = User.query.filter_by(email=session["user_email"]).first()
	ids = (request.get_json(silent=True) or {}).get("ids") or []
	if not isinstance(ids, list):
		ids = []
	q = Notification.query.filter(Notification.user_id == user.id)
	if ids:
		q = q.filter(Notification.id.in_(ids))
	for n in q.all():
		n.is_read = True
	db.session.commit()
	return {"ok": True}


# Seed a notification (dev/testing)
@app.route("/dev/notify")
def dev_notify():
	if not session.get("user_email"):
		return redirect(url_for("login"))
	user = User.query.filter_by(email=session["user_email"]).first()
	db.session.add(Notification(user_id=user.id, message="New destination deals available!", kind="info"))
	db.session.commit()
	flash("Test notification created.", "success")
	return redirect(url_for("dashboard"))




# API route for adding suggestions to trip
@app.route("/api/suggestions/add-to-trip", methods=["POST"])
def add_suggestion_to_trip():
	if not session.get("user_email"):
		return {"ok": False, "error": "Not logged in"}, 401
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		return {"ok": False, "error": "User not found"}, 404
	
	try:
		data = request.get_json()
		if not data:
			return {"ok": False, "error": "No data provided"}, 400
		
		destination_name = data.get("name", "").strip()
		destination_location = data.get("location", "").strip()
		trip_id = data.get("trip_id")
		
		if not destination_name:
			return {"ok": False, "error": "Destination name required"}, 400
		
		# If trip_id is provided, use that specific trip
		if trip_id:
			target_trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
			if not target_trip:
				return {"ok": False, "error": "Trip not found"}, 404
		else:
			# Find user's most recent planned or in-progress trip
			target_trip = Trip.query.filter_by(user_id=user.id)\
				.filter(Trip.status.in_(["planned", "in_progress"]))\
				.order_by(Trip.created_at.desc()).first()
		
		if not target_trip:
			# Create a new trip if none exists
			target_trip = Trip(
				user_id=user.id,
				title=f"Trip to {destination_name}",
				status="planned"
			)
			db.session.add(target_trip)
			db.session.flush()  # Get trip ID
		
		# Check if destination already exists in trip
		existing = TripDestination.query.filter_by(
			trip_id=target_trip.id,
			name=destination_name
		).first()
		
		if existing:
			return {"ok": False, "error": "Destination already in trip"}, 409
		
		# Add destination to trip
		max_order = db.session.query(db.func.max(TripDestination.order_index))\
			.filter_by(trip_id=target_trip.id).scalar() or -1
		max_sequence = db.session.query(db.func.max(TripDestination.sequence))\
			.filter_by(trip_id=target_trip.id).scalar() or 0
		
		new_destination = TripDestination(
			trip_id=target_trip.id,
			name=destination_name,
			city=destination_location,
			order_index=max_order + 1,
			sequence=max_sequence + 1
		)
		
		db.session.add(new_destination)
		db.session.commit()
		
		return {
			"ok": True,
			"message": f"Added {destination_name} to {target_trip.title}",
			"trip_id": target_trip.id,
			"trip_title": target_trip.title
		}
		
	except Exception as e:
		db.session.rollback()
		return {"ok": False, "error": str(e)}, 500

# API route for adding suggestions to wishlist
@app.route("/api/suggestions/add-to-wishlist", methods=["POST"])
def add_suggestion_to_wishlist():
	if not session.get("user_email"):
		return {"ok": False, "error": "Not logged in"}, 401
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		return {"ok": False, "error": "User not found"}, 404
	
	try:
		data = request.get_json()
		if not data:
			return {"ok": False, "error": "No data provided"}, 400
		
		title = data.get("name", "").strip()
		location = data.get("location", "").strip()
		description = data.get("description", "").strip()
		
		if not title:
			return {"ok": False, "error": "Title required"}, 400
		
		# Check if item already exists in wishlist
		existing = WishlistItem.query.filter_by(
			user_id=user.id,
			title=title
		).first()
		
		if existing:
			return {"ok": False, "error": "Item already in wishlist"}, 409
		
		# Add to wishlist
		wishlist_item = WishlistItem(
			user_id=user.id,
			title=title,
			city=location,
			description=description,
			created_at=datetime.utcnow()
		)
		
		db.session.add(wishlist_item)
		db.session.commit()
		
		return {
			"ok": True,
			"message": f"Added {title} to wishlist"
		}
		
	except Exception as e:
		db.session.rollback()
		return {"ok": False, "error": str(e)}, 500

@app.route("/api/trips/<int:trip_id>/delete", methods=["DELETE"])
def delete_trip(trip_id):
	if not session.get("user_email"):
		return {"ok": False, "error": "Not logged in"}, 401
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		return {"ok": False, "error": "User not found"}, 404
	
	try:
		# Find the trip
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			return {"ok": False, "error": "Trip not found"}, 404
		
		# Delete all trip destinations first (foreign key constraint)
		TripDestination.query.filter_by(trip_id=trip_id).delete()
		
		# Delete the trip
		db.session.delete(trip)
		db.session.commit()
		
		return {
			"ok": True,
			"message": "Trip deleted successfully"
		}
		
	except Exception as e:
		db.session.rollback()
		print(f"Error deleting trip: {str(e)}")
		return {"ok": False, "error": "Failed to delete trip"}, 500

@app.route("/api/trips/<int:trip_id>/update", methods=["PUT"])
def update_trip(trip_id):
	if not session.get("user_email"):
		return {"ok": False, "error": "Not logged in"}, 401
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		return {"ok": False, "error": "User not found"}, 404
	
	try:
		data = request.get_json()
		if not data:
			return {"ok": False, "error": "No data provided"}, 400
		
		# Find the trip
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			return {"ok": False, "error": "Trip not found"}, 404
		
		field = data.get("field")
		value = data.get("value")
		
		if not field:
			return {"ok": False, "error": "Field is required"}, 400
		
		# Update the appropriate field
		if field == "title":
			trip.title = value
		elif field == "start_date":
			from datetime import datetime
			trip.start_date = datetime.strptime(value, "%Y-%m-%d").date() if value else None
		elif field == "end_date":
			from datetime import datetime
			trip.end_date = datetime.strptime(value, "%Y-%m-%d").date() if value else None
		elif field == "budget":
			trip.budget = float(value) if value else 0.0
		else:
			return {"ok": False, "error": "Invalid field"}, 400
		
		db.session.commit()
		
		return {
			"ok": True,
			"message": f"Trip {field.replace('_', ' ')} updated successfully"
		}
		
	except Exception as e:
		db.session.rollback()
		print(f"Error updating trip: {str(e)}")
		return {"ok": False, "error": "Failed to update trip"}, 500

@app.route("/user/edit-profile")
def edit_profile():
	if not session.get("user_email"):
		flash("Please log in to access this page.", "error")
		return redirect(url_for("login"))
	# current_user is injected via context_processor; no extra data needed
	return render_template("user/edit_profile.html")


@app.route("/user/update-profile", methods=["POST"])
def update_profile():
	if not session.get("user_email"):
		flash("Please log in to update your profile.", "error")
		return redirect(url_for("login"))
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		flash("User not found.", "error")
		return redirect(url_for("login"))
	
	try:
		# Extract fields we support
		full_name = (request.form.get("fullName") or "").strip()
		email = (request.form.get("email") or "").strip().lower()
		phone = (request.form.get("phone") or "").strip() or None
		city = (request.form.get("city") or "").strip() or None
		state = (request.form.get("state") or "").strip() or None
		country = (request.form.get("country") or "").strip() or None
		bio = (request.form.get("bio") or "").strip() or None
		date_of_birth_str = (request.form.get("dateOfBirth") or "").strip()
		
		# Handle travel preferences checkboxes
		preferences = request.form.getlist("preferences[]")
		preferences_json = None
		if preferences:
			import json
			preferences_json = json.dumps(preferences)
		
		print(f"Debug - Travel preferences received: {preferences}")
		print(f"Debug - Preferences JSON: {preferences_json}")
		
		# Handle profile picture upload
		profile_picture_file = request.files.get('profilePicture')
		if profile_picture_file and profile_picture_file.filename:
			print(f"Processing file upload: {profile_picture_file.filename}")
			# Check file type
			allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
			filename = profile_picture_file.filename.lower()
			if '.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions:
				# Create uploads directory if it doesn't exist
				import os
				upload_folder = os.path.join(app.static_folder, 'uploads', 'profiles')
				os.makedirs(upload_folder, exist_ok=True)
				print(f"Upload folder created/verified: {upload_folder}")
				
				# Generate unique filename
				import uuid
				file_extension = filename.rsplit('.', 1)[1]
				unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
				file_path = os.path.join(upload_folder, unique_filename)
				
				# Save file to filesystem (NOT database)
				profile_picture_file.save(file_path)
				relative_path = f"uploads/profiles/{unique_filename}"
				
				# Store only the relative path in database (NOT the file content)
				user.profile_picture = relative_path
				
				print(f"✓ File saved to filesystem: {file_path}")
				print(f"✓ Path stored in database: {relative_path}")
				print(f"✓ File size: {os.path.getsize(file_path)} bytes")
				flash("Profile picture uploaded successfully!", "success")
			else:
				flash("Invalid file type. Please upload PNG, JPG, JPEG, or GIF files only.", "error")
				return redirect(url_for("edit_profile"))
		
		# Update name: best-effort split
		if full_name:
			parts = full_name.split()
			user.first_name = parts[0]
			user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
		
		# Email change: ensure unique
		if email and email != user.email:
			if User.query.filter(User.email == email, User.id != user.id).first():
				flash("That email is already in use.", "error")
				return redirect(url_for("edit_profile"))
			user.email = email
			session["user_email"] = email
		
		# Parse date of birth
		date_of_birth = None
		if date_of_birth_str:
			try:
				from datetime import datetime
				date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
			except ValueError:
				flash("Invalid date format for date of birth.", "error")
				return redirect(url_for("edit_profile"))
		
		# Update other fields
		user.phone = phone
		user.city = city
		user.state = state
		user.country = country
		user.bio = bio
		user.date_of_birth = date_of_birth
		user.travel_preferences = preferences_json
		
		print(f"Debug - Saving preferences to DB: {preferences_json}")
		
		db.session.commit()
		flash("Profile updated successfully!", "success")
		
	except Exception as e:
		db.session.rollback()
		flash("An error occurred while updating your profile. Please try again.", "error")
		print(f"Profile update error: {e}")
	
	return redirect(url_for("profile_settings"))

# Debug route to verify file upload functionality
@app.route("/debug/uploads")
def debug_uploads():
	if not session.get("user_email"):
		return "Please log in first"
	
	import os
	upload_folder = os.path.join(app.static_folder, 'uploads', 'profiles')
	try:
		files = os.listdir(upload_folder)
		user = User.query.filter_by(email=session["user_email"]).first()
		return f"""
		<h3>Upload Debug Info</h3>
		<p><strong>Upload folder:</strong> {upload_folder}</p>
		<p><strong>Files in folder:</strong> {files}</p>
		<p><strong>Current user profile_picture field:</strong> {user.profile_picture if user else 'No user'}</p>
		<p><strong>Upload folder exists:</strong> {os.path.exists(upload_folder)}</p>
		<hr>
		<p>This confirms files are stored in filesystem, not database!</p>
		"""
	except Exception as e:
		return f"Error: {e}"

# ===== FAST SEARCH & SORTING API ENDPOINTS =====

@app.route("/api/search/trips", methods=["GET"])
def fast_trip_search():
	"""Optimized trip search API with fast algorithms"""
	if not session.get("user_email"):
		return {"ok": False, "error": "Not logged in"}, 401
	
	user = User.query.filter_by(email=session["user_email"]).first()
	if not user:
		return {"ok": False, "error": "User not found"}, 404
	
	try:
		# Get search parameters
		query = request.args.get('q', '').strip()
		status = request.args.get('status', '').strip()
		sort_by = request.args.get('sort', 'created_at')
		order = request.args.get('order', 'desc')
		page = int(request.args.get('page', 1))
		limit = int(request.args.get('limit', 20))
		
		# Use optimized search method
		from models import Trip, SearchUtils
		
		trips = Trip.search_trips(
			user_id=user.id,
			query=query if query else None,
			status=status if status else None,
			limit=limit,
			offset=(page - 1) * limit,
			order_by=sort_by,
			order_dir=order
		)
		
		# Convert to JSON format
		trip_data = []
		for trip in trips:
			destinations = [
				{
					'name': dest.name,
					'city': dest.city,
					'country': dest.country
				} for dest in trip.destinations
			]
			
			trip_data.append({
				'id': trip.id,
				'title': trip.title,
				'status': trip.status,
				'start_date': trip.start_date.isoformat() if trip.start_date else None,
				'end_date': trip.end_date.isoformat() if trip.end_date else None,
				'created_at': trip.created_at.isoformat(),
				'budget': trip.budget,
				'priority': trip.priority,
				'destinations': destinations
			})
		
		# Get total count for pagination
		total_query = Trip.query.filter_by(user_id=user.id)
		if query:
			total_query = total_query.filter(
				db.or_(
					Trip.title.ilike(f'%{query}%'),
					Trip.destinations.any(TripDestination.name.ilike(f'%{query}%'))
				)
			)
		if status:
			total_query = total_query.filter(Trip.status == status)
		
		total = total_query.count()
		
		return {
			"ok": True,
			"trips": trip_data,
			"pagination": {
				"total": total,
				"page": page,
				"limit": limit,
				"pages": (total + limit - 1) // limit,
				"has_next": page * limit < total,
				"has_prev": page > 1
			},
			"search_info": {
				"query": query,
				"status": status,
				"sort_by": sort_by,
				"order": order
			}
		}
		
	except Exception as e:
		print(f"Error in fast trip search: {str(e)}")
		return {"ok": False, "error": "Search failed"}, 500

@app.route("/api/recommendations/<int:item_id>/rate", methods=["POST"])
def rate_recommendation(item_id):
    """Update the rating for a recommendation item"""
    if not session.get("user_email"):
        return {"ok": False, "error": "Not logged in"}, 401
    
    user = User.query.filter_by(email=session["user_email"]).first()
    if not user:
        return {"ok": False, "error": "User not found"}, 404
        
    try:
        data = request.get_json()
        if not data or 'rating' not in data:
            return {"ok": False, "error": "Rating is required"}, 400
            
        rating = float(data['rating'])
        if rating < 1.0 or rating > 5.0:
            return {"ok": False, "error": "Rating must be between 1 and 5"}, 400
            
        item = WishlistItem.query.filter_by(id=item_id, user_id=user.id).first()
        if not item:
            return {"ok": False, "error": "Item not found"}, 404
            
        item.rating = rating
        item.last_rated = datetime.utcnow()
        db.session.commit()
        
        return {
            "ok": True,
            "item": {
                "id": item.id,
                "title": item.title,
                "rating": item.rating,
                "last_rated": item.last_rated.isoformat()
            }
        }
        
    except ValueError:
        return {"ok": False, "error": "Invalid rating value"}, 400
    except Exception as e:
        print(f"Error updating rating: {str(e)}")
        db.session.rollback()
        return {"ok": False, "error": "Failed to update rating"}, 500

@app.route("/api/search/recommendations", methods=["GET"])
def fast_recommendation_search():
	"""Optimized recommendation search API"""
	try:
		# Get search parameters
		query = request.args.get('q', '').strip()
		tag = request.args.get('tag', '').strip()
		sort_by = request.args.get('sort', 'rating')
		order = request.args.get('order', 'desc')
		page = int(request.args.get('page', 1))
		limit = int(request.args.get('limit', 20))
		
		# Use optimized search method
		from models import WishlistItem
		
		recommendations = WishlistItem.search_recommendations(
			query=query if query else None,
			tag=tag if tag else None,
			limit=limit,
			offset=(page - 1) * limit,
			order_by=sort_by,
			order_dir=order
		)
		
		# Convert to JSON format
		rec_data = []
		for rec in recommendations:
			rec_data.append({
				'id': rec.id,
				'title': rec.title,
				'city': rec.city,
				'country': rec.country,
				'image_url': rec.image_url,
				'tags': rec.tags,
				'rating': rec.rating,
				'created_at': rec.created_at.isoformat()
			})
		
		return {
			"ok": True,
			"recommendations": rec_data,
			"search_info": {
				"query": query,
				"tag": tag,
				"sort_by": sort_by,
				"order": order
			}
		}
		
	except Exception as e:
		print(f"Error in fast recommendation search: {str(e)}")
		return {"ok": False, "error": "Search failed"}, 500

@app.route("/api/trips")
def get_user_trips():
    """Get all trips for the current user"""
    if not session.get("user_email"):
        return {"ok": False, "error": "Not logged in"}, 401

    user = User.query.filter_by(email=session["user_email"]).first()
    if not user:
        return {"ok": False, "error": "User not found"}, 404

    try:
        trips = Trip.query.filter_by(user_id=user.id).order_by(Trip.created_at.desc()).all()
        trips_data = []

        for trip in trips:
            destinations = [
                {
                    'name': dest.name,
                    'city': dest.city,
                    'country': dest.country
                } for dest in trip.destinations
            ]

            trips_data.append({
                'id': trip.id,
                'title': trip.title,
                'status': trip.status,
                'start_date': trip.start_date.isoformat() if trip.start_date else None,
                'end_date': trip.end_date.isoformat() if trip.end_date else None,
                'created_at': trip.created_at.isoformat(),
                'budget': float(trip.budget) if trip.budget else 0.0,
                'destinations': destinations,
                'destinations_count': len(destinations)
            })

        return jsonify({"ok": True, "trips": trips_data})

    except Exception as e:
        print(f"Error fetching trips: {str(e)}")
        return {"ok": False, "error": "Failed to fetch trips"}, 500

@app.route("/api/budget/estimate")
def estimate_budget():
    """Get budget estimation based on destinations and duration"""
    try:
        days = int(request.args.get('days', 1))
        destinations = request.args.get('destinations', '').split(',')
        
        if not destinations or not destinations[0]:
            return jsonify({"error": "At least one destination is required"}), 400

        import requests
        from datetime import datetime
        import json
        
        # Cache results in memory for 1 hour to avoid hitting API limits
        cache_file = 'cost_data_cache.json'
        try:
            with open(cache_file) as f:
                cache = json.load(f)
                if datetime.now().timestamp() - cache['timestamp'] < 3600:  # 1 hour cache
                    city_costs = cache['data']
                else:
                    raise Exception("Cache expired")
        except:
            # Fetch current India GDP per capita from World Bank API (2023 data)
            wb_response = requests.get(
                "https://api.worldbank.org/v2/country/IND/indicator/NY.GDP.PCAP.CD?format=json&per_page=1&mrnev=1"
            )
            india_gdp = float(wb_response.json()[1][0]['value'])
            
            # Get exchange rate
            exchange_response = requests.get(
                "https://open.er-api.com/v6/latest/USD"
            )
            usd_to_inr = exchange_response.json()['rates']['INR']
            
            # City cost factors (relative to national average)
            city_costs = {
                'Mumbai': 1.8,
                'Delhi': 1.6,
                'Bangalore': 1.7,
                'Chennai': 1.5,
                'Kolkata': 1.4,
                'Jaipur': 1.3,
                'Goa': 1.6,
                'Udaipur': 1.4,
                'Agra': 1.3,
                'Varanasi': 1.2,
                'Kochi': 1.4,
                'Shimla': 1.5,
                'Manali': 1.5,
                'Rishikesh': 1.3,
                'Amritsar': 1.3,
                'Pune': 1.5,
                'Hyderabad': 1.5,
                'Ahmedabad': 1.4,
            }
            
            # Calculate base daily cost (using GDP per capita as reference)
            base_daily_cost = (india_gdp * usd_to_inr) / 365 * 2  # Assuming tourism cost is 2x daily GDP
            
            # Update costs with real values
            for city in city_costs:
                city_costs[city] = round(base_daily_cost * city_costs[city])
            
            # Cache the results
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().timestamp(),
                    'data': city_costs
                }, f)

        # Calculate total budget
        total_cost = 0
        used_costs = []
        
        for dest in destinations:
            dest = dest.strip()
            # Find closest matching city
            matching_city = None
            max_similarity = 0
            
            for city in city_costs:
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, dest.lower(), city.lower()).ratio()
                if similarity > max_similarity and similarity > 0.6:  # 60% match threshold
                    max_similarity = similarity
                    matching_city = city
            
            if matching_city:
                daily_cost = city_costs[matching_city]
                used_costs.append(daily_cost)
            else:
                # Use average if city not found
                daily_cost = sum(city_costs.values()) / len(city_costs)
                used_costs.append(daily_cost)
        
        # Calculate total with adjustments
        avg_daily_cost = sum(used_costs) / len(used_costs)
        if len(destinations) > 1:
            # Add 20% for transportation between cities
            avg_daily_cost *= 1.2
        
        # Add seasonal adjustment
        current_month = datetime.now().month
        if 11 <= current_month <= 2:  # Peak season (winter)
            avg_daily_cost *= 1.3
        elif 6 <= current_month <= 8:  # Off season (monsoon)
            avg_daily_cost *= 0.8
            
        total_cost = round(avg_daily_cost * days)
        
        # Add breakdown for transparency
        breakdown = {
            "base_daily_cost": round(avg_daily_cost),
            "duration_days": days,
            "seasonal_factor": "peak" if 11 <= current_month <= 2 else "off" if 6 <= current_month <= 8 else "regular",
            "multi_city_factor": 1.2 if len(destinations) > 1 else 1.0
        }
        
        return jsonify({
            "ok": True,
            "estimate_inr": total_cost,
            "per_day_inr": round(avg_daily_cost),
            "breakdown": breakdown,
            "cities_found": [d for d in destinations if any(SequenceMatcher(None, d.lower(), c.lower()).ratio() > 0.6 for c in city_costs)]
        })
            
    except Exception as e:
        print(f"Budget estimation error: {str(e)}")
        return jsonify({"error": "Failed to estimate budget"}), 500

@app.route("/api/weather")
def get_weather():
    """Get weather data for a location using OpenWeatherMap API"""
    try:
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        if not lat or not lng:
            return jsonify({"error": "Latitude and longitude are required"}), 400
            
        # Using OpenWeatherMap API
        OPENWEATHER_API_KEY = "3422434e8bc000623c0f52a0b92c64ac"
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric"
        
        import requests
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            return jsonify({
                "temp": data["main"]["temp"],
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"]
            })
        else:
            # Fallback to mock data if API fails
            return jsonify({
                "temp": 25,
                "weather": "Clear",
                "description": "clear sky",
                "humidity": 60
            })
            
    except Exception as e:
        print(f"Weather API error: {str(e)}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@app.route("/api/sort/trips", methods=["POST"])
def fast_trip_sort():
	"""Fast client-side sorting using optimized algorithms"""
	if not session.get("user_email"):
		return {"ok": False, "error": "Not logged in"}, 401
	
	try:
		data = request.get_json()
		trip_ids = data.get('trip_ids', [])
		sort_by = data.get('sort_by', 'created_at')
		reverse = data.get('reverse', False)
		
		# Get trips
		from models import Trip, SearchUtils
		trips = Trip.query.filter(Trip.id.in_(trip_ids)).all()
		
		# Apply fast sorting
		sorted_trips = SearchUtils.quick_sort_trips(trips, sort_by, reverse)
		
		# Return sorted IDs
		sorted_ids = [trip.id for trip in sorted_trips]
		
		return {
			"ok": True,
			"sorted_ids": sorted_ids,
			"sort_info": {
				"sort_by": sort_by,
				"reverse": reverse,
				"count": len(sorted_ids)
			}
		}
		
	except Exception as e:
		print(f"Error in fast trip sort: {str(e)}")
		return {"ok": False, "error": "Sort failed"}, 500

@app.route("/api/cache/refresh", methods=["POST"])
def refresh_cache():
	"""Refresh cached data for better performance"""
	if not session.get("user_email"):
		return {"ok": False, "error": "Not logged in"}, 401
	
	try:
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user:
			return {"ok": False, "error": "User not found"}, 404
		
		# Refresh user data with optimized queries
		trips = Trip.query.filter_by(user_id=user.id).options(
			db.joinedload(Trip.destinations)
		).order_by(Trip.created_at.desc()).all()
		
		recommendations = WishlistItem.query.order_by(
			WishlistItem.rating.desc()
		).limit(20).all()
		
		notifications = Notification.query.filter_by(user_id=user.id).filter_by(
			is_read=False
		).order_by(Notification.created_at.desc()).limit(10).all()
		
		return {
			"ok": True,
			"cache_info": {
				"trips_count": len(trips),
				"recommendations_count": len(recommendations),
				"unread_notifications": len(notifications),
				"refresh_time": datetime.utcnow().isoformat()
			}
		}
		
	except Exception as e:
		print(f"Error refreshing cache: {str(e)}")
		return {"ok": False, "error": "Cache refresh failed"}, 500

@app.route('/api/trips/<int:trip_id>', methods=['GET'])
def get_trip_details(trip_id):
	"""Get details for a specific trip"""
	if "user_email" not in session:
		return {"ok": False, "error": "Not logged in"}, 401
	
	try:
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user:
			return {"ok": False, "error": "User not found"}, 404
		
		# Verify trip ownership
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			return {"ok": False, "error": "Trip not found"}, 404
		
		trip_data = {
			'id': trip.id,
			'title': trip.title,
			'start_date': trip.start_date.isoformat() if trip.start_date else None,
			'end_date': trip.end_date.isoformat() if trip.end_date else None,
			'budget': trip.budget,
			'status': trip.status,
			'created_at': trip.created_at.isoformat() if trip.created_at else None
		}
		
		return {"ok": True, "trip": trip_data}
		
	except Exception as e:
		print(f"Error getting trip details: {str(e)}")
		return {"ok": False, "error": "Failed to get trip details"}, 500

@app.route('/api/trips/<int:trip_id>/cities', methods=['GET'])
def get_trip_cities(trip_id):
	"""Get cities/destinations for a specific trip"""
	if "user_email" not in session:
		return {"ok": False, "error": "Not logged in"}, 401
	
	try:
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user:
			return {"ok": False, "error": "User not found"}, 404
		
		# Verify trip ownership
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			return {"ok": False, "error": "Trip not found"}, 404
		
		# Get all destinations for this trip
		destinations = TripDestination.query.filter_by(trip_id=trip_id).order_by(
			TripDestination.order_index.asc()
		).all()
		
		cities = []
		for dest in destinations:
			cities.append({
				'id': dest.id,
				'name': dest.name,
				'city': dest.city,
				'country': dest.country,
				'order_index': dest.order_index,
				'budget': dest.budget,
				'date_range': dest.date_range
			})
		
		return {"ok": True, "cities": cities}
		
	except Exception as e:
		print(f"Error getting trip cities: {str(e)}")
		return {"ok": False, "error": "Failed to get cities"}, 500

# ========== EXPENSE MANAGEMENT ROUTES ==========

@app.route('/api/trips/<int:trip_id>/expenses', methods=['GET'])
def get_trip_expenses(trip_id):
	"""Get all expenses for a specific trip with category breakdown"""
	if "user_email" not in session:
		return {"ok": False, "error": "Not logged in"}, 401
	
	try:
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user:
			return {"ok": False, "error": "User not found"}, 404
		
		# Verify trip ownership
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			return {"ok": False, "error": "Trip not found"}, 404
		
		# Get all expenses for this trip
		expenses = TripExpense.query.filter_by(trip_id=trip_id).order_by(
			TripExpense.expense_date.desc()
		).all()
		
		# Calculate category breakdown
		category_totals = {}
		daily_totals = {}
		total_amount = 0
		
		for expense in expenses:
			# Category totals
			if expense.category not in category_totals:
				category_totals[expense.category] = 0
			category_totals[expense.category] += expense.amount
			
			# Daily totals
			date_str = expense.expense_date.strftime('%Y-%m-%d')
			if date_str not in daily_totals:
				daily_totals[date_str] = 0
			daily_totals[date_str] += expense.amount
			
			total_amount += expense.amount
		
		# Format expenses for response
		expense_list = []
		for expense in expenses:
			expense_list.append({
				'id': expense.id,
				'category': expense.category,
				'amount': expense.amount,
				'description': expense.description,
				'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
				'created_at': expense.created_at.strftime('%Y-%m-%d %H:%M'),
				'destination_id': expense.destination_id
			})
		
		# Calculate average daily spending
		num_days = len(daily_totals) if daily_totals else 1
		avg_daily_spend = total_amount / num_days
		
		return {
			"ok": True,
			"expenses": expense_list,
			"summary": {
				"total_amount": total_amount,
				"category_breakdown": category_totals,
				"daily_totals": daily_totals,
				"avg_daily_spend": round(avg_daily_spend, 2),
				"num_expenses": len(expenses),
				"num_days": num_days
			}
		}
		
	except Exception as e:
		print(f"Error getting trip expenses: {str(e)}")
		return {"ok": False, "error": "Failed to get expenses"}, 500

@app.route('/api/trips/<int:trip_id>/expenses', methods=['POST'])
def add_trip_expense(trip_id):
	"""Add a new expense to a trip"""
	if "user_email" not in session:
		return {"ok": False, "error": "Not logged in"}, 401
	
	try:
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user:
			return {"ok": False, "error": "User not found"}, 404
		
		# Verify trip ownership
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			return {"ok": False, "error": "Trip not found"}, 404
		
		data = request.get_json()
		if not data:
			return {"ok": False, "error": "No data provided"}, 400
		
		# Validate required fields
		required_fields = ['category', 'amount', 'expense_date']
		for field in required_fields:
			if field not in data or not data[field]:
				return {"ok": False, "error": f"Missing required field: {field}"}, 400
		
		# Validate category
		valid_categories = ['accommodation', 'meals', 'transport', 'activities', 'shopping', 'other']
		if data['category'] not in valid_categories:
			return {"ok": False, "error": "Invalid category"}, 400
		
		# Parse date
		try:
			expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
		except ValueError:
			return {"ok": False, "error": "Invalid date format. Use YYYY-MM-DD"}, 400
		
		# Create new expense
		expense = TripExpense(
			trip_id=trip_id,
			category=data['category'],
			amount=float(data['amount']),
			description=data.get('description', ''),
			expense_date=expense_date,
			destination_id=data.get('destination_id')
		)
		
		db.session.add(expense)
		db.session.commit()
		
		return {
			"ok": True,
			"expense": {
				'id': expense.id,
				'category': expense.category,
				'amount': expense.amount,
				'description': expense.description,
				'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
				'created_at': expense.created_at.strftime('%Y-%m-%d %H:%M'),
				'destination_id': expense.destination_id
			}
		}
		
	except ValueError as e:
		return {"ok": False, "error": "Invalid amount format"}, 400
	except Exception as e:
		print(f"Error adding expense: {str(e)}")
		return {"ok": False, "error": "Failed to add expense"}, 500

@app.route('/api/trips/<int:trip_id>/expenses/<int:expense_id>', methods=['DELETE'])
def delete_trip_expense(trip_id, expense_id):
	"""Delete a specific expense"""
	if "user_email" not in session:
		return {"ok": False, "error": "Not logged in"}, 401
	
	try:
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user:
			return {"ok": False, "error": "User not found"}, 404
		
		# Verify trip ownership
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		if not trip:
			return {"ok": False, "error": "Trip not found"}, 404
		
		# Find and delete expense
		expense = TripExpense.query.filter_by(id=expense_id, trip_id=trip_id).first()
		if not expense:
			return {"ok": False, "error": "Expense not found"}, 404
		
		db.session.delete(expense)
		db.session.commit()
		
		return {"ok": True, "message": "Expense deleted successfully"}
		
	except Exception as e:
		print(f"Error deleting expense: {str(e)}")
		return {"ok": False, "error": "Failed to delete expense"}, 500

@app.route('/trip/<int:trip_id>/budget')
def trip_budget_detailed(trip_id):
	"""Budget breakdown page for a specific trip"""
	if "user_email" not in session:
		flash("Please log in to view trip budget.", "error")
		return redirect(url_for("login"))
	
	try:
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user:
			flash("User not found.", "error")
			return redirect(url_for("login"))
		
		# Get trip with destinations
		trip = Trip.query.filter_by(id=trip_id, user_id=user.id).first()
		
		if not trip:
			flash("Trip not found.", "error")
			return redirect(url_for("dashboard"))
		
		return render_template("trip/budget_breakdown.html", trip=trip, user=user)
		
	except Exception as e:
		print(f"Error loading budget breakdown: {str(e)}")
		flash("Error loading budget breakdown.", "error")
		return redirect(url_for("dashboard"))

# ====================================
# ADMIN ROUTES & ANALYTICS DASHBOARD
# ====================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
	"""Admin login with database authentication"""
	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')
		
		# Check database for admin user
		user = User.query.filter_by(email=email).first()
		
		if user and user.check_password(password) and user.is_admin:
			session['user_email'] = email
			session['user_id'] = user.id
			flash('Admin login successful!', 'success')
			return redirect(url_for('admin_dashboard'))
		else:
			flash('Invalid admin credentials or insufficient privileges.', 'error')
	
	return '''
	<!DOCTYPE html>
	<html>
	<head>
		<title>Admin Login - GlobeTrotter</title>
		<script src="https://cdn.tailwindcss.com"></script>
	</head>
	<body class="bg-gray-100 min-h-screen flex items-center justify-center">
		<div class="bg-white p-8 rounded-lg shadow-md w-96">
			<h2 class="text-2xl font-bold mb-6 text-center">Admin Login</h2>
			<form method="POST">
				<div class="mb-4">
					<label class="block text-gray-700 text-sm font-bold mb-2">Email:</label>
					<input type="email" name="email" value="admin@12345" 
						   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500">
				</div>
				<div class="mb-6">
					<label class="block text-gray-700 text-sm font-bold mb-2">Password:</label>
					<input type="password" name="password" value="12345"
						   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500">
				</div>
				<button type="submit" 
						class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
					Login as Admin
				</button>
			</form>
			<p class="text-center mt-4 text-sm text-gray-600">
				<a href="/" class="text-blue-500 hover:underline">← Back to Main Site</a>
			</p>
		</div>
	</body>
	</html>
	'''

def admin_required(f):
	"""Decorator to require admin access"""
	from functools import wraps
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if "user_email" not in session:
			flash("Please log in to access admin panel.", "error")
			return redirect(url_for("admin_login"))
		
		user = User.query.filter_by(email=session["user_email"]).first()
		if not user or not getattr(user, 'is_admin', False):
			flash("Admin access required.", "error")
			return redirect(url_for("admin_login"))
		
		return f(*args, **kwargs)
	return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
	"""Main admin dashboard with analytics overview"""
	try:
		# Get overview statistics
		total_users = User.query.count()
		active_users = User.query.filter_by(is_active=True).count()
		total_trips = Trip.query.count()
		
		# Handle expenses query safely
		try:
			total_expenses = db.session.query(db.func.sum(TripExpense.amount)).scalar() or 0
		except Exception:
			total_expenses = 0
		
		# Recent activity (last 30 days)
		thirty_days_ago = datetime.utcnow() - timedelta(days=30)
		recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
		recent_trips = Trip.query.filter(Trip.created_at >= thirty_days_ago).count()
		
		# User growth trend (last 6 months)
		user_growth = []
		for i in range(6):
			month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
			month_end = month_start + timedelta(days=32)
			month_end = month_end.replace(day=1) - timedelta(days=1)
			
			count = User.query.filter(
				User.created_at >= month_start,
				User.created_at <= month_end
			).count()
			
			user_growth.append({
				'month': month_start.strftime('%b %Y'),
				'count': count
			})
		
		user_growth.reverse()
		
		# Trip status distribution (we'll use created date as proxy for status)
		recent_trips_count = Trip.query.filter(Trip.created_at >= thirty_days_ago).count()
		older_trips_count = Trip.query.filter(Trip.created_at < thirty_days_ago).count()
		trip_stats = {
			'planned': recent_trips_count,  # Recent trips as "planned"
			'in_progress': min(3, total_trips // 3),  # Sample in-progress
			'completed': older_trips_count
		}
		
		# Popular destinations (top 10)
		popular_destinations_query = db.session.query(
			TripDestination.name,
			db.func.count(TripDestination.id).label('count')
		).filter(
			TripDestination.name.isnot(None)
		).group_by(
			TripDestination.name
		).order_by(
			db.func.count(TripDestination.id).desc()
		).limit(10).all()
		
		# Convert to dictionaries to avoid JSON serialization issues
		popular_destinations = [
			{'name': dest.name, 'count': dest.count} 
			for dest in popular_destinations_query
		]
		
		# Budget analytics
		budget_by_month_query = db.session.query(
			db.func.strftime('%Y-%m', Trip.created_at).label('month'),
			db.func.avg(Trip.budget).label('avg_budget'),
			db.func.sum(Trip.budget).label('total_budget')
		).filter(
			Trip.budget.isnot(None)
		).group_by(
			db.func.strftime('%Y-%m', Trip.created_at)
		).order_by('month').limit(12).all()
		
		# Convert to dictionaries
		budget_analytics = [
			{'month': row.month, 'avg_budget': float(row.avg_budget or 0), 'total_budget': float(row.total_budget or 0)}
			for row in budget_by_month_query
		]
		
		# Expense categories breakdown
		try:
			expense_categories_query = db.session.query(
				TripExpense.category,
				db.func.sum(TripExpense.amount).label('total'),
				db.func.count(TripExpense.id).label('count')
			).group_by(TripExpense.category).all()
			
			# Convert to dictionaries
			expense_categories = [
				{'category': row.category, 'total': float(row.total or 0), 'count': row.count}
				for row in expense_categories_query
			]
		except Exception:
			expense_categories = []
		
		# Recent activities
		recent_activity = []
		
		# Recent users
		new_users = User.query.order_by(User.created_at.desc()).limit(5).all()
		for user in new_users:
			recent_activity.append({
				'type': 'user_signup',
				'user': f"{user.first_name} {user.last_name}",
				'description': 'New user signed up',
				'date': user.created_at
			})
		
		# Recent trips
		new_trips = Trip.query.order_by(Trip.created_at.desc()).limit(5).all()
		for trip in new_trips:
			user = User.query.get(trip.user_id)
			recent_activity.append({
				'type': 'trip_created',
				'user': f"{user.first_name} {user.last_name}" if user else 'Unknown',
				'description': f'Created trip: {trip.title}',
				'date': trip.created_at
			})
		
		# Sort recent activity by date
		recent_activity.sort(key=lambda x: x['date'], reverse=True)
		recent_activity = recent_activity[:10]
		
		# Calculate verified users
		verified_users = User.query.filter_by(is_email_verified=True).count()
		
		# Enhanced expense analytics
		try:
			total_expense_count = TripExpense.query.count()
			avg_expense_per_trip = (total_expenses / total_trips) if total_trips > 0 else 0
			
			# Monthly expense trends (last 6 months)
			expense_trends = []
			expense_months = []
			expense_amounts = []
			for i in range(6):
				month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
				month_end = month_start + timedelta(days=32)
				month_end = month_end.replace(day=1) - timedelta(days=1)
				
				monthly_expenses = db.session.query(db.func.sum(TripExpense.amount)).filter(
					TripExpense.expense_date >= month_start.date(),
					TripExpense.expense_date <= month_end.date()
				).scalar() or 0
				
				expense_trends.append({
					'month': month_start.strftime('%b %Y'),
					'amount': float(monthly_expenses)
				})
				expense_months.append(month_start.strftime('%b %Y'))
				expense_amounts.append(float(monthly_expenses))
			
			expense_trends.reverse()
			expense_months.reverse()
			expense_amounts.reverse()
			
			# Budget vs Actual comparison
			budget_comparison_query = db.session.query(
				Trip.title,
				Trip.budget,
				db.func.coalesce(db.func.sum(TripExpense.amount), 0).label('actual_spent')
			).outerjoin(TripExpense).group_by(Trip.id).limit(10).all()
			
			budget_comparison = {
				'trip_names': [row.title[:15] + '...' if len(row.title) > 15 else row.title for row in budget_comparison_query],
				'budgets': [float(row.budget) if row.budget else 0 for row in budget_comparison_query],
				'actual': [float(row.actual_spent) for row in budget_comparison_query]
			}
			
		except Exception:
			total_expense_count = 0
			avg_expense_per_trip = 0
			expense_trends = []
			expense_months = []
			expense_amounts = []
			budget_comparison = {'trip_names': [], 'budgets': [], 'actual': []}
		
		analytics_data = {
			'overview': {
				'total_users': total_users,
				'active_users': active_users,
				'verified_users': verified_users,
				'total_trips': total_trips,
				'total_expenses': total_expenses,
				'total_expense_count': total_expense_count,
				'avg_expense_per_trip': avg_expense_per_trip,
				'recent_users': recent_users,
				'recent_trips': recent_trips
			},
			'user_growth': user_growth,
			'trip_stats': trip_stats,
			'popular_destinations': popular_destinations,
			'budget_analytics': budget_analytics,
			'expense_categories': expense_categories,
			'expense_trends': {
				'months': expense_months,
				'amounts': expense_amounts,
				'data': expense_trends
			},
			'budget_comparison': budget_comparison,
			'recent_activity': recent_activity
		}
		
		return render_template('admin/admin_dashboard.html', analytics=analytics_data)
		
	except Exception as e:
		print(f"Error loading admin dashboard: {str(e)}")
		flash("Error loading admin dashboard.", "error")
		# Return a simple error page instead of redirecting to user dashboard
		return render_template('admin/admin_dashboard.html', analytics={
			'overview': {'total_users': 0, 'active_users': 0, 'total_trips': 0, 'total_expenses': 0, 'recent_users': 0, 'recent_trips': 0},
			'user_growth': [], 'trip_stats': {}, 'popular_destinations': [], 
			'budget_analytics': [], 'expense_categories': [], 'recent_activity': []
		})

@app.route('/admin/users')
@admin_required
def admin_users():
	"""User management page"""
	try:
		page = request.args.get('page', 1, type=int)
		search = request.args.get('search', '')
		status = request.args.get('status', '')
		
		# Base query
		query = User.query
		
		# Apply filters
		if search:
			query = query.filter(
				db.or_(
					User.first_name.ilike(f'%{search}%'),
					User.last_name.ilike(f'%{search}%'),
					User.email.ilike(f'%{search}%')
				)
			)
		
		if status == 'active':
			query = query.filter_by(is_active=True)
		elif status == 'inactive':
			query = query.filter_by(is_active=False)
		elif status == 'admin':
			query = query.filter_by(is_admin=True)
		
		# Pagination
		users = query.order_by(User.created_at.desc()).paginate(
			page=page, per_page=20, error_out=False
		)
		
		return render_template('admin/users.html', users=users, search=search, status=status)
		
	except Exception as e:
		print(f"Error loading users page: {str(e)}")
		flash("Error loading users.", "error")
		return redirect(url_for("admin_dashboard"))

@app.route('/admin/trips')
@admin_required
def admin_trips():
	"""Trip management and analytics page"""
	try:
		page = request.args.get('page', 1, type=int)
		search = request.args.get('search', '')
		status = request.args.get('status', '')
		budget_range = request.args.get('budget_range', '')
		
		# Base query with user relationship
		query = Trip.query.join(User)
		
		# Apply filters
		if search:
			query = query.filter(
				db.or_(
					Trip.title.ilike(f'%{search}%'),
					User.first_name.ilike(f'%{search}%'),
					User.last_name.ilike(f'%{search}%')
				)
			)
		
		# Note: No status filter since the current schema doesn't have status field
		
		# Pagination
		trips = query.order_by(Trip.created_at.desc()).paginate(
			page=page, per_page=20, error_out=False
		)
		
		return render_template('admin/trips.html', trips=trips, search=search, status=status, budget_range=budget_range)
		
	except Exception as e:
		print(f"Error loading trips page: {str(e)}")
		flash("Error loading trips.", "error")
		return redirect(url_for("admin_dashboard"))

@app.route('/admin/api/user/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_user_status(user_id):
	"""Toggle user active status"""
	try:
		user = User.query.get_or_404(user_id)
		user.is_active = not user.is_active
		db.session.commit()
		
		status = "activated" if user.is_active else "deactivated"
		return jsonify({
			'success': True,
			'message': f'User {user.email} has been {status}.',
			'is_active': user.is_active
		})
		
	except Exception as e:
		return jsonify({
			'success': False,
			'message': f'Error updating user status: {str(e)}'
		}), 500

@app.route('/admin/api/user/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def admin_toggle_user_admin(user_id):
	"""Toggle user admin status"""
	try:
		user = User.query.get_or_404(user_id)
		user.is_admin = not user.is_admin
		db.session.commit()
		
		status = "granted" if user.is_admin else "revoked"
		return jsonify({
			'success': True,
			'message': f'Admin access {status} for {user.email}.',
			'is_admin': user.is_admin
		})
		
	except Exception as e:
		return jsonify({
			'success': False,
			'message': f'Error updating admin status: {str(e)}'
		}), 500

@app.route('/admin/api/user/<int:user_id>/toggle-verification', methods=['POST'])
@admin_required  
def admin_toggle_email_verification(user_id):
	"""Toggle user email verification status"""
	try:
		user = User.query.get_or_404(user_id)
		
		# Toggle verification status
		user.is_email_verified = not user.is_email_verified
		
		# Clear OTP if marking as verified
		if user.is_email_verified:
			user.clear_otp()
		
		db.session.commit()
		
		return jsonify({
			'success': True,
			'message': f'Email verification {"enabled" if user.is_email_verified else "disabled"} for {user.email}',
			'is_email_verified': user.is_email_verified
		}), 200
	except Exception as e:
		return jsonify({
			'success': False,
			'message': f'Error toggling email verification: {str(e)}'
		}), 500

@app.route('/admin/api/user/<int:user_id>/resend-verification', methods=['POST'])
@admin_required
def admin_resend_verification(user_id):
	"""Admin can resend verification email to user"""
	try:
		user = User.query.get_or_404(user_id)
		
		if user.is_email_verified:
			return jsonify({
				'success': False,
				'message': 'User email is already verified'
			}), 400
		
		# Generate new OTP
		otp_code = user.generate_otp()
		db.session.commit()
		
		# Send OTP email
		if send_otp_email(user, otp_code):
			return jsonify({
				'success': True,
				'message': f'Verification email sent to {user.email}'
			}), 200
		else:
			return jsonify({
				'success': False,
				'message': 'Failed to send verification email'
			}), 500
			
	except Exception as e:
		return jsonify({
			'success': False,
			'message': f'Error resending verification: {str(e)}'
		}), 500

@app.route('/admin/api/analytics/data')
@admin_required
def admin_analytics_data():
	"""API endpoint for real-time analytics data"""
	try:
		# User analytics
		total_users = User.query.count()
		active_users = User.query.filter_by(is_active=True).count()
		admin_users = User.query.filter_by(is_admin=True).count()
		verified_users = User.query.filter_by(is_email_verified=True).count()
		unverified_users = total_users - verified_users
		
		# Trip analytics
		total_trips = Trip.query.count()
		planned_trips = Trip.query.filter_by(status='planned').count()
		active_trips = Trip.query.filter_by(status='in_progress').count()
		completed_trips = Trip.query.filter_by(status='completed').count()
		
		# Financial analytics
		total_budget = db.session.query(db.func.sum(Trip.budget)).scalar() or 0
		try:
			total_expenses = db.session.query(db.func.sum(TripExpense.amount)).scalar() or 0
		except Exception:
			total_expenses = 0
		
		# Growth analytics (last 7 days)
		week_ago = datetime.utcnow() - timedelta(days=7)
		new_users_week = User.query.filter(User.created_at >= week_ago).count()
		new_trips_week = Trip.query.filter(Trip.created_at >= week_ago).count()
		
		# Popular destinations this month
		month_ago = datetime.utcnow() - timedelta(days=30)
		popular_destinations = db.session.query(
			TripDestination.city,
			db.func.count(TripDestination.id).label('count')
		).join(Trip).filter(
			Trip.created_at >= month_ago,
			TripDestination.city.isnot(None)
		).group_by(TripDestination.city).order_by(
			db.func.count(TripDestination.id).desc()
		).limit(5).all()
		
		return jsonify({
			'users': {
				'total': total_users,
				'active': active_users,
				'admin': admin_users,
				'verified': verified_users,
				'unverified': unverified_users,
				'new_this_week': new_users_week
			},
			'trips': {
				'total': total_trips,
				'planned': planned_trips,
				'active': active_trips,
				'completed': completed_trips,
				'new_this_week': new_trips_week
			},
			'financial': {
				'total_budget': total_budget,
				'total_expenses': total_expenses,
				'savings_rate': ((total_budget - total_expenses) / total_budget * 100) if total_budget > 0 else 0
			},
			'popular_destinations': [{'city': dest.city, 'count': dest.count} for dest in popular_destinations]
		})
		
	except Exception as e:
		return jsonify({'error': str(e)}), 500

# Health check endpoint for Render and monitoring services
@app.route("/health")
@app.route("/healthz")
def health_check():
	"""Health check endpoint for monitoring and Render"""
	try:
		# Check database connection
		db.session.execute(db.text('SELECT 1'))
		db_status = "healthy"
	except Exception as e:
		db_status = f"unhealthy: {str(e)}"
	
	health_data = {
		"status": "healthy" if db_status == "healthy" else "degraded",
		"database": db_status,
		"environment": "production" if IS_PRODUCTION else "development",
		"timestamp": datetime.utcnow().isoformat()
	}
	
	status_code = 200 if db_status == "healthy" else 503
	return jsonify(health_data), status_code

# Simple ping endpoint
@app.route("/ping")
def ping():
	"""Simple ping endpoint to keep app awake"""
	return jsonify({"message": "pong", "timestamp": datetime.utcnow().isoformat()}), 200

if __name__ == "__main__":
	# Ensure DB tables exist
	with app.app_context():
		db.create_all()
	# For local development. In production, use a WSGI server (gunicorn/uwsgi) instead.
	app.run(debug=True)

