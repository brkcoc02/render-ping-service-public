import time
import random
import requests
import logging
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Dict, Any, Optional
from app.models.ping_data import ping_data
from config import Config
from urllib.parse import urlparse
import socket

# Add lock for scheduled ping protection
SCHEDULED_PING_LOCK = Lock()
NEXT_SCHEDULED_PING = datetime.now()

def is_valid_url(url: str) -> bool:
    """Validate URL for security.

    Args:
        url: The URL string to validate

    Returns:
        bool: True if URL is valid and safe, False otherwise
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        # Only allow http and https schemes
        if result.scheme not in ('http', 'https'):
            return False
        # Prevent internal network access
        host = result.hostname
        if host:
            ip = socket.gethostbyname(host)
            ip_parts = ip.split('.')
            if (ip.startswith('127.') or  # Localhost
                ip.startswith('10.') or   # Private network
                ip.startswith('172.16.') or  # Private network
                ip.startswith('192.168.') or  # Private network
                ip == '0.0.0.0' or
                ip == '255.255.255.255'):
                return False
            return True
    except Exception:
        return False

def get_ist_time() -> str:
    """Get current time in Indian Standard Time (IST)."""
    utc_time = datetime.utcnow()
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%H:%M:%S")

def get_remaining_time() -> float:
    """Calculate remaining time until next scheduled ping."""
    now = datetime.now()
    remaining = max(0, (NEXT_SCHEDULED_PING - now).total_seconds())
    return max(0, remaining)

def ping(url: str, retries: int = 3) -> dict:
    """Pings the given URL and logs the result, with retries."""
    if not is_valid_url(url):
        logging.error(f"Invalid or unsafe URL attempted: {url}")
        return {"status": "failure", "error": "Invalid or unsafe URL"}

    # Enforce maximum retries
    retries = min(retries, 3)
    
    for attempt in range(1, retries + 1):
        try:
            start_time = time.time()
            response = requests.get(
                url, 
                timeout=(5, 30),
                headers={
                    'User-Agent': 'Render-Ping-Service/1.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'close'
                },
                verify=True,
                allow_redirects=False  # Prevent open redirects
            )
            response_time = round((time.time() - start_time) * 1000)
            
            # Consider only 2xx status codes as success
            status = "Success" if 200 <= response.status_code < 300 else "Failure"
            logging.info(f"Pinged {url}, Status Code: {response.status_code}, Response Time: {response_time}ms")
            
            # Record the ping result
            ping_data.record_ping(url, status, response_time, response.status_code)
            
            return {
                "status": "success", 
                "response_time": response_time,
                "status_code": response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Attempt {attempt} failed to ping {url}: {e}")
            if attempt < retries:
                sleep_time = min(2 * attempt, 10)  # Cap at 10 seconds
                logging.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
                continue
            
            logging.error(f"All {retries} attempts to ping {url} failed.")
            ping_data.record_ping(url, "Failure", 0, "Error")
            # Sanitize error message to prevent information disclosure
            return {"status": "failure", "response_time": 0, "error": "Request failed"}

def run_pinger() -> None:
    """Background thread function to run scheduled pings."""
    global NEXT_SCHEDULED_PING
    while True:
        try:
            with SCHEDULED_PING_LOCK:
                logging.info("Starting a new ping cycle...")
                # Create a safe copy of URLs and validate each
                urls = [url for url in Config.TARGET_URLS if is_valid_url(url)]
                random.shuffle(urls)
            
                for url in urls:
                logging.info(f"Pinging URL: {url}")
                ping(url)
                # Use system random for security-sensitive operations
                interval = random.SystemRandom().randint(5, 15)
                logging.info(f"Sleeping for {interval} seconds before the next ping...")
                time.sleep(interval)
                
            cycle_sleep_time = random.SystemRandom().randint(
                Config.PING_INTERVAL_MIN, 
                Config.PING_INTERVAL_MAX
            )
            NEXT_SCHEDULED_PING = datetime.now() + timedelta(seconds=cycle_sleep_time)
            logging.info(f"Completed all pings. Sleeping for {cycle_sleep_time} seconds...")
            time.sleep(cycle_sleep_time)

# Start the background pinger thread
def start_pinger():
    pinger_thread = Thread(target=run_pinger)
    pinger_thread.daemon = True
    pinger_thread.start()
