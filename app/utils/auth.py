from functools import wraps
from flask import request, Response
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
        # First check for session cookie
        if request.cookies.get('session'):
            return f(*args, **kwargs)

        # Fall back to basic auth
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return unauthorized()
        return f(*args, **kwargs)
    return decorated

def unauthorized():
    """Send a 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )
