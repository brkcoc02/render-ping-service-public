from functools import wraps
import time
from flask import request, jsonify
from config import Config

# Rate limiting storage
request_history = {}

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        now = time.time()
        remote_addr = request.remote_addr
        
        if remote_addr not in request_history:
            request_history[remote_addr] = []
        
        # Clean old requests
        request_history[remote_addr] = [t for t in request_history[remote_addr] 
                                      if t > now - Config.RATE_LIMIT_WINDOW]
        
        if len(request_history[remote_addr]) >= Config.MAX_REQUESTS:
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        request_history[remote_addr].append(now)
        return f(*args, **kwargs)
    return decorated_function
