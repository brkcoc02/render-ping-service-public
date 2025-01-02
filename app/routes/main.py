from flask import render_template, send_from_directory, request, redirect, url_for
from app.routes import main_bp
from app.utils.auth import requires_auth

@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main_bp.route('/dashboard', methods=['GET'])
@requires_auth
def dashboard():
    return render_template('index.html')

@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')
