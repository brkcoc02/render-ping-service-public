from flask import jsonify
from datetime import datetime, timedelta
from app.routes import ping_bp
from app.utils.auth import requires_auth
from app.utils.rate_limit import rate_limit
from app.services.ping_service import ping, get_remaining_time
from app.models.ping_data import ping_data
from config import Config

@ping_bp.route('/check-scheduled-ping')
@requires_auth
@rate_limit
def check_scheduled_ping():
    """Check if a scheduled ping is imminent."""
    remaining_time = get_remaining_time()
    return jsonify({
        'imminent': remaining_time <= 10,
        'remainingTime': remaining_time
    })

@ping_bp.route('/ping/<int:url_index>')
@requires_auth
@rate_limit
def manual_ping(url_index):
    """Handle manual ping requests."""
    try:
        if 0 <= url_index < len(Config.TARGET_URLS):
            url = Config.TARGET_URLS[url_index]
            
            remaining_time = get_remaining_time()
            if remaining_time <= 60:
                return jsonify({
                    "status": "wait", 
                    "message": "Scheduled ping imminent",
                    "remainingTime": remaining_time
                }), 423
            
            result = ping(url)
            return jsonify({
                "status": "success", 
                "message": f"Successfully pinged {url}", 
                "data": result
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Invalid URL index"
            }), 400
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@ping_bp.route('/ping-all')
@requires_auth
@rate_limit
def ping_all():
    """Handle ping all request."""
    try:
        remaining_time = get_remaining_time()
        if remaining_time <= 60:
             return jsonify({
                 "status": "wait", 
                 "message": "Scheduled ping imminent",
                 "remainingTime": remaining_time
             }), 423
        
        results = []
        for url in Config.TARGET_URLS:
            result = ping(url)
            results.append({"url": url, "result": result})
            time.sleep(1)  # Small delay between pings
            
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@ping_bp.route('/api/ping-history')
@requires_auth
def get_ping_history():
    """Return the complete ping history for all URLs"""
    history = {}
    for url in Config.TARGET_URLS:
        history[url] = ping_data.get_history(url)
    return jsonify(history)
