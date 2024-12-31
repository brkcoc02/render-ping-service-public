from flask import jsonify, make_response, request, Response
from app.routes import auth_bp
from app.utils.auth import check_auth, generate_session_token, requires_auth

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle login requests and set secure session cookie."""
    data = request.get_json()
    if data and check_auth(data.get('username'), data.get('password')):
        resp = make_response(jsonify({'status': 'success'}))
        resp.set_cookie(
            'session',
            value=generate_session_token(),
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=300,  # 5 minutes expiry
            path='/',     # Restrict cookie to root path
            domain=None,  # Restrict to same domain only
        )
        return resp
    return unauthorized()

@auth_bp.route('/logout', methods=['POST'])
@requires_auth
def logout():
    """Handle logout requests."""
    resp = make_response(jsonify({'status': 'success'}))
    resp.delete_cookie('session', path='/', domain=None)
    return resp

def unauthorized():
    """Send a 401 response without triggering browser's basic auth."""
    return jsonify({'error': 'Authentication required'}), 401
    
