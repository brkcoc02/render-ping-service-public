from functools import wraps
from flask import request, Response, jsonify, redirect, url_for, render_template, current_app
from secrets import token_urlsafe
from config import Config
import hashlib
import hmac

def generate_session_token():
    """Generate a secure random token for session."""
    token = token_urlsafe(32)
    # Add timestamp to token to enable absolute session expiry validation
    from time import time
    timestamp = str(int(time()))
    token_data = f"{token}.{timestamp}"
    signature = hmac.new(
        current_app.config['SECRET_KEY'].encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{token_data}.{signature}"

def check_auth(username, password):
    """Check if the username and password match."""
    if not username or not password:
        return False
    return hmac.compare_digest(username, Config.USERNAME) and hmac.compare_digest(password, Config.PASSPHRASE)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
            
        # First check for session cookie
        session_cookie = request.cookies.get('session')
        if session_cookie and validate_session_token(session_cookie):
            return f(*args, **kwargs)

        # Check if request is for API endpoint
        if request.path.startswith('/api/') or request.path == '/check-scheduled-ping':
            return jsonify({'error': 'Authentication required'}), 401
        
        # For HTML requests, force authentication
        return redirect(url_for('auth.login')), 401
    return decorated

def validate_session_token(token):
    """Validate the session token's signature."""
    try:
        token_part, timestamp, signature = token.rsplit('.', 2)
        # Check absolute session expiry (5 minutes)
        from time import time
        if int(time()) - int(timestamp) > 300:  # 5 minutes in seconds
            return False

        token_data = f"{token_part}.{timestamp}"
        expected_signature = hmac.new(
            current_app.config['SECRET_KEY'].encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except (ValueError, AttributeError, TypeError):
        return False
        
