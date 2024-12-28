import os
from secrets import token_urlsafe

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', token_urlsafe(32))
    
    # Authentication credentials
    USERNAME = os.environ.get('AUTH_USERNAME')
    PASSPHRASE = os.environ.get('AUTH_PASSPHRASE')

    # URLs to monitor - moved to environment variables
    MEDIAFLOW_URL = os.environ.get('MEDIAFLOW_PROXY_URL')
    MEDIAFLOW_DOCS_URL = f"{MEDIAFLOW_URL}/docs" if MEDIAFLOW_URL else None
    JSON_PLACEHOLDER_URL = os.environ.get('JSON_PLACEHOLDER_URL', 'https://jsonplaceholder.typicode.com/posts')
    
    # URLs to monitor
    TARGET_URLS = [
        MEDIAFLOW_URL,
        MEDIAFLOW_DOCS_URL,
        JSON_PLACEHOLDER_URL,
    ]
    
    # Table IDs corresponding to URLs
    TABLE_IDS = ["table1", "table2", "table3"]
    
    # History and monitoring constants
    MAX_HISTORY_PER_URL = 20
    PING_INTERVAL_MIN = 120
    PING_INTERVAL_MAX = 600
    
    # Rate limiting configuration
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_REQUESTS = 60       # maximum requests per window
