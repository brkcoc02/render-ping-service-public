from flask import jsonify, make_response, request, Response, render_template, redirect, url_for
from app.routes import auth_bp
from app.utils.auth import check_auth, generate_session_token, requires_auth

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle login requests and set secure session cookie."""
    # Show login form for GET requests
    if request.method == 'GET':
        return render_template('login.html')

    # Handle both JSON and form data for POST requests
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        
    if check_auth(username, password):
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
        # Redirect to index for form submissions
        if not request.is_json:
            return redirect(url_for('main.serve_index'))
        return resp

    # Different error responses for JSON vs form
    if request.is_json:
        return unauthorized()
    return render_template('login.html', error="Invalid credentials")

@auth_bp.route('/logout', methods=['POST'])
@requires_auth
def logout():
    """Handle logout requests."""
    resp = make_response(jsonify({'status': 'success'}))
    resp.delete_cookie('session', path='/', domain=None)
    if not request.is_json:
        return redirect(url_for('auth.login'))
    return resp

def unauthorized():
    """Send a 401 response without triggering browser's basic auth."""
    return jsonify({'error': 'Authentication required'}), 401
    
