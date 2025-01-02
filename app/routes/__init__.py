from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
ping_bp = Blueprint('ping', __name__)

# Import routes after blueprint creation to avoid circular imports
from app.routes import main, auth, ping

def configure_routes(app):
  """Configure and register all blueprints for the application."""
  # Register blueprints
  app.register_blueprint(main_bp)
  app.register_blueprint(auth_bp, url_prefix='/auth')
  app.register_blueprint(ping_bp, url_prefix='/ping')

  return app
  
