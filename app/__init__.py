from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, 
                static_folder='../static',    # Point to static folder in root
                template_folder='../templates' # Point to templates folder in root
    )
    app.config.from_object(config_class)
    
    # Register blueprints (we'll add these later)
    from app.routes import main_bp
    from app.routes import auth_bp
    from app.routes import ping_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ping_bp)
    
    return app
