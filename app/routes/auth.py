from flask import jsonify, make_response, request, Response
from app.routes import auth_bp
from app.utils.auth import check_auth, generate_session_token, requires_auth

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle login requests and set secure session cookie."""
    auth = request.authorization
    if auth and check_auth(auth.username, auth.password):
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
    """Send a 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )