from app import create_app
from app.app.services.ping_service import start_pinger
from app.app.routes import configure_routes
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ping_service.log")
    ]
)

app = create_app()

# Start the background pinger thread
start_pinger()

if __name__ == "__main__":
    try:
        # Development server
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        logging.info("Ping Service stopped by user. Exiting...")
        exit(0)
