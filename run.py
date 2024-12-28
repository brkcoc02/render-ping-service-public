from app import create_app
from app.services.ping_service import start_pinger
import logging

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

if __name__ == "__main__":
    try:
        # Start the background pinger thread
        start_pinger()
        # Run the Flask application
        app.run(host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        logging.info("Ping Service stopped by user. Exiting...")
        exit(0)
