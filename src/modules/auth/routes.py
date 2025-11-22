"""
Authentication routes.

This module defines routes for user authentication including
login, register, and logout.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from modules.auth.service import AuthService
from utils.responses import success_response, error_response
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.

    GET: Display login form.
    POST: Process login credentials.
    """
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('auth/login.html')

    # Handle POST request
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        flash('Username and password are required', 'danger')
        return render_template('auth/login.html')

    try:
        result = auth_service.login(username, password)
        
        # Store user info in session
        session['user_id'] = result['user']['_id']
        session['username'] = result['user']['username']
        session['user_role'] = result['user']['role']
        session['full_name'] = result['user']['full_name']

        flash(f"Welcome back, {result['user']['full_name'] or result['user']['username']}!", 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))

    except ValueError as e:
        flash(str(e), 'danger')
        return render_template('auth/login.html')
    except Exception as e:
        logger.error(f"Login error: {e}")
        flash('An error occurred during login', 'danger')
        return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.

    GET: Display registration form.
    POST: Process registration.
    """
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('auth/register.html')

    # Handle POST request
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    full_name = request.form.get('full_name', '').strip()

    # Validation
    if not all([username, email, password, confirm_password]):
        flash('All fields are required', 'danger')
        return render_template('auth/register.html')

    if password != confirm_password:
        flash('Passwords do not match', 'danger')
        return render_template('auth/register.html')

    try:
        result = auth_service.register_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role='viewer'  # Default role for new registrations
        )

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    except ValueError as e:
        flash(str(e), 'danger')
        return render_template('auth/register.html')
    except Exception as e:
        logger.error(f"Registration error: {e}")
        flash('An error occurred during registration', 'danger')
        return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    """User logout route."""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('auth.login'))


# API endpoints for JWT-based authentication

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """
    API login endpoint (returns JWT token).

    Returns JSON response with user data and JWT token.
    """
    data = request.get_json()
    
    if not data:
        return error_response("Invalid request data", status_code=400)

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error_response("Username and password are required", status_code=400)

    try:
        result = auth_service.login(username, password)
        return success_response(result, "Login successful")

    except ValueError as e:
        return error_response(str(e), status_code=401)
    except Exception as e:
        logger.error(f"API login error: {e}")
        return error_response("An error occurred during login", status_code=500)


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """
    API registration endpoint.

    Returns JSON response with user data.
    """
    data = request.get_json()
    
    if not data:
        return error_response("Invalid request data", status_code=400)

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()

    if not all([username, email, password]):
        return error_response("Username, email, and password are required", status_code=400)

    try:
        result = auth_service.register_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role='viewer'
        )

        return success_response(result, "Registration successful", status_code=201)

    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"API registration error: {e}")
        return error_response("An error occurred during registration", status_code=500)


@auth_bp.route('/api/verify', methods=['POST'])
def api_verify_token():
    """
    API endpoint to verify JWT token.

    Returns user data if token is valid.
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response("Authorization header required", status_code=401)

    token = auth_header.split(' ')[1]

    try:
        payload = auth_service.verify_token(token)
        user = auth_service.get_user_by_id(payload['user_id'])
        
        if user:
            return success_response({'user': user}, "Token is valid")
        else:
            return error_response("User not found", status_code=404)

    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return error_response("Invalid or expired token", status_code=401)


# Password Reset Routes

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot password route - Request OTP.

    GET: Display forgot password form.
    POST: Send OTP to email.
    """
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')

    # Handle POST request
    email = request.form.get('email', '').strip()

    if not email:
        flash('Email is required', 'danger')
        return render_template('auth/forgot_password.html')

    try:
        result = auth_service.request_password_reset(email)
        flash('If your email is registered, you will receive an OTP shortly.', 'success')
        return redirect(url_for('auth.verify_otp', email=email))

    except ValueError as e:
        flash(str(e), 'danger')
        return render_template('auth/forgot_password.html')
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        flash('An error occurred. Please try again later.', 'danger')
        return render_template('auth/forgot_password.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """
    Verify OTP route.

    GET: Display OTP verification form.
    POST: Verify OTP and proceed to password reset.
    """
    email = request.args.get('email', '').strip()

    if request.method == 'GET':
        if not email:
            flash('Email is required', 'warning')
            return redirect(url_for('auth.forgot_password'))
        return render_template('auth/verify_otp.html', email=email)

    # Handle POST request
    email = request.form.get('email', '').strip()
    otp_code = request.form.get('otp', '').strip()

    if not email or not otp_code:
        flash('Email and OTP are required', 'danger')
        return render_template('auth/verify_otp.html', email=email)

    try:
        result = auth_service.verify_otp(email, otp_code)
        session['reset_token'] = result['reset_token']
        flash('OTP verified! Please set your new password.', 'success')
        return redirect(url_for('auth.reset_password'))

    except ValueError as e:
        flash(str(e), 'danger')
        return render_template('auth/verify_otp.html', email=email)
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return render_template('auth/verify_otp.html', email=email)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Reset password route.

    GET: Display new password form.
    POST: Reset password with new password.
    """
    reset_token = session.get('reset_token')

    if not reset_token:
        flash('Invalid reset session. Please start over.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'GET':
        return render_template('auth/reset_password.html')

    # Handle POST request
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not new_password or not confirm_password:
        flash('Both password fields are required', 'danger')
        return render_template('auth/reset_password.html')

    if new_password != confirm_password:
        flash('Passwords do not match', 'danger')
        return render_template('auth/reset_password.html')

    try:
        result = auth_service.reset_password(reset_token, new_password)
        session.pop('reset_token', None)  # Clear reset token from session
        flash('Password reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    except ValueError as e:
        flash(str(e), 'danger')
        return render_template('auth/reset_password.html')
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return render_template('auth/reset_password.html')


# API endpoints for password reset

@auth_bp.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """
    API endpoint to request password reset OTP.

    Returns success message.
    """
    data = request.get_json()
    
    if not data:
        return error_response("Invalid request data", status_code=400)

    email = data.get('email', '').strip()

    if not email:
        return error_response("Email is required", status_code=400)

    try:
        result = auth_service.request_password_reset(email)
        return success_response(result, result['message'])

    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"API forgot password error: {e}")
        return error_response("An error occurred", status_code=500)


@auth_bp.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    """
    API endpoint to verify OTP.

    Returns reset token.
    """
    data = request.get_json()
    
    if not data:
        return error_response("Invalid request data", status_code=400)

    email = data.get('email', '').strip()
    otp_code = data.get('otp', '').strip()

    if not email or not otp_code:
        return error_response("Email and OTP are required", status_code=400)

    try:
        result = auth_service.verify_otp(email, otp_code)
        return success_response(result, "OTP verified successfully")

    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"API OTP verification error: {e}")
        return error_response("An error occurred", status_code=500)


@auth_bp.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """
    API endpoint to reset password.

    Returns success message.
    """
    data = request.get_json()
    
    if not data:
        return error_response("Invalid request data", status_code=400)

    reset_token = data.get('reset_token', '').strip()
    new_password = data.get('new_password', '')

    if not reset_token or not new_password:
        return error_response("Reset token and new password are required", status_code=400)

    try:
        result = auth_service.reset_password(reset_token, new_password)
        return success_response(result, "Password reset successfully")

    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"API password reset error: {e}")
        return error_response("An error occurred", status_code=500)
