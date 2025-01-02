from flask import render_template, send_from_directory, request
from app.routes import main_bp
from app.utils.auth import requires_auth

@main_bp.route('/', methods=['GET'])
@requires_auth
def serve_index():
    return render_template('index.html')

@main_bp.route('/favicon.ico')
def serve_favicon():
    return send_from_directory('static', 'favicon.ico')
