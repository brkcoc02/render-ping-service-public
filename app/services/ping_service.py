import time
import random
import requests
import logging
from datetime import datetime, timedelta
from threading import Thread, Lock
from app.models.ping_data import ping_data
from config import Config

# Add lock for scheduled ping protection
SCHEDULED_PING_LOCK = Lock()
NEXT_SCHEDULED_PING = datetime.now()

def get_ist_time():
    """Get current time in Indian Standard Time (IST)."""
    utc_time = datetime.utcnow()
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%H:%M:%S")

def get_remaining_time():
    """Calculate remaining time until next scheduled ping."""
    now = datetime.now()
    remaining = max(0, (NEXT_SCHEDULED_PING - now).total_seconds())
    return max(0, remaining)

def ping(url, retries=3):
    """Pings the given URL and logs the result, with retries."""
    for attempt in range(1, retries + 1):
        try:
            start_time = time.time()
            response = requests.get(
                url, 
                timeout=(5, 30),
                headers={'User-Agent': 'Render-Ping-Service/1.0'},
                verify=True,
                allow_redirects=True
            )
            response_time = round((time.time() - start_time) * 1000)
            
            status = "Success" if response.status_code == 200 else "Failure"
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
                sleep_time = 2 * attempt
                logging.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
                continue
            
            logging.error(f"All {retries} attempts to ping {url} failed.")
            ping_data.record_ping(url, "Failure", 0, "Error")
            return {"status": "failure", "response_time": 0, "error": str(e)}

def run_pinger():
    """Background thread function to run scheduled pings."""
    global NEXT_SCHEDULED_PING
    while True:
        with SCHEDULED_PING_LOCK:
            logging.info("Starting a new ping cycle...")
            urls = list(Config.TARGET_URLS)
            random.shuffle(urls)
            
            for url in urls:
                logging.info(f"Pinging URL: {url}")
                ping(url)
                interval = random.randint(5, 15)
                logging.info(f"Sleeping for {interval} seconds before the next ping...")
                time.sleep(interval)
                
            cycle_sleep_time = random.randint(
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
