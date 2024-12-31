from functools import wraps
from flask import request, Response, jsonify, redirect, url_for, render_template
from secrets import token_urlsafe
from config import Config

def generate_session_token():
    """Generate a secure random token for session."""
    return token_urlsafe(32)

def check_auth(username, password):
    """Check if the username and password match."""
    return username == Config.USERNAME and password == Config.PASSPHRASE

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Handle HEAD requests first
        if request.method == 'HEAD':
            return '', 200
            
        # First check for session cookie
        if request.cookies.get('session'):
            return f(*args, **kwargs)

        # Check if request is for API endpoint
        if request.path.startswith('/api/') or request.path == '/check-scheduled-ping':
            return jsonify({'error': 'Authentication required'}), 401

        # For HTML requests, redirect to login page
        return render_template('index.html')
    return decorated
