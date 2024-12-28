from collections import deque
from datetime import datetime
from config import Config

class PingData:
    def __init__(self):
        # Initialize data structures for storing ping results
        self.ping_history = {}  # Stores complete ping history for each URL
        self.response_times = {url: deque(maxlen=100) for url in Config.TARGET_URLS}
        self.incidents = {url: deque(maxlen=1000) for url in Config.TARGET_URLS}
        self.uptime_stats = {url: {'success': 0, 'total': 0} for url in Config.TARGET_URLS}

    def record_ping(self, url, status, response_time, status_code):
        """Record a ping result in the history"""
        if url not in self.ping_history:
            self.ping_history[url] = []
            
        # Update history
        self.ping_history[url].append({
            'url': url,
            'timestamp': datetime.utcnow().isoformat(),
            'response_time': response_time,
            'status': status,
            'status_code': status_code,
            'uptime': self.calculate_uptime(url)
        })

        # Maintain history limit
        if len(self.ping_history[url]) > Config.MAX_HISTORY_PER_URL:
            self.ping_history[url] = self.ping_history[url][-Config.MAX_HISTORY_PER_URL:]

        # Update other metrics
        if response_time > 0:
            self.response_times[url].append(response_time)
        
        self.uptime_stats[url]['total'] += 1
        if status == "Success":
            self.uptime_stats[url]['success'] += 1
        else:
            self.incidents[url].append({
                'time': datetime.utcnow(),
                'status_code': status_code
            })

    def calculate_uptime(self, url):
        """Calculate uptime percentage for a given URL"""
        stats = self.uptime_stats[url]
        if stats['total'] == 0:
            return 100.0
        return round((stats['success'] / stats['total']) * 100, 2)

    def get_history(self, url):
        """Get the complete history for a URL"""
        return self.ping_history.get(url, [])

# Create a global instance
ping_data = PingData()
