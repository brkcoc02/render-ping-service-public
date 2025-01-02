from flask import jsonify, make_response, request, Response, render_template, redirect, url_for
from app.routes import auth_bp
from app.utils.auth import check_auth, generate_session_token, requires_auth, validate_session_token

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login requests and set secure session cookie."""
    # Show login form for GET requests
    if request.method == 'GET':
        # Check if already authenticated
        session_cookie = request.cookies.get('session')
        if session_cookie and validate_session_token(session_cookie):
            return redirect(url_for('main.dashboard'))
        # If not authenticated, render the login template
        return render_template('index.html')

    # Handle both JSON and form data for POST requests
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    if not username or not password:
        return unauthorized()
        
    if check_auth(username, password):
        resp = make_response(jsonify({'status': 'success'}))
        resp.set_cookie(
            'session',
            value=generate_session_token(username),
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=300,  # 5 minutes expiry
            path='/',     # Restrict cookie to root path
            domain=None,  # Restrict to same domain only
        )
        resp.headers['Location'] = url_for('main.dashboard')
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
    
