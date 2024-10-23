# rate_limiter.py
import time
import requests
from functools import wraps
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, calls_per_minute):
        self.calls_per_minute = calls_per_minute
        self.interval = 60 / calls_per_minute
        self.last_call = 0

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            time_since_last_call = now - self.last_call
            if time_since_last_call < self.interval:
                time.sleep(self.interval - time_since_last_call)
            self.last_call = time.time()
            return func(*args, **kwargs)
        return wrapper

@RateLimiter(calls_per_minute=5)
def make_api_request(method, url, **kwargs):
    response = requests.request(method, url, **kwargs)
    return response
