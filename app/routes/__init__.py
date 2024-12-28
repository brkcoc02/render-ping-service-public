from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
ping_bp = Blueprint('ping', __name__)

# Import routes after blueprint creation to avoid circular imports
from app.routes import main, auth, ping
