import requests
import os
from dotenv import load_dotenv
from functools import wraps, lru_cache
import json
import redis
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

base_url = os.getenv("OPEN_EXCHANGE_RATES_BASE_URL")
app_id = os.getenv("OPEN_EXCHANGE_RATES_APP_ID")

# Initialize Redis client with error handling
redis_port = 6379
try:
    redis_client = redis.Redis(host="localhost", port=redis_port, db=0)
    redis_client.ping()  # Test the connection
    use_redis = True
    logger.info("Redis connection established successfully.")
except (ImportError, redis.exceptions.ConnectionError):
    logger.warning(
        f"Redis is not available on port {redis_port}. Using LRU cache instead."
    )
    use_redis = False


def timed_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        if use_redis:

            @wraps(func)
            def wrapped_func(*args, **kwargs):
                cache_key = f"{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Redis cache hit for {cache_key}")
                    return json.loads(cached_data)

                logger.debug(f"Redis cache miss for {cache_key}")
                result = func(*args, **kwargs)
                if result is not None:
                    redis_client.setex(cache_key, seconds, json.dumps(result))
                return result

        else:

            @lru_cache(maxsize=maxsize)
            @wraps(func)
            def wrapped_func(*args, **kwargs):
                logger.debug(f"LRU cache access for {func.__name__}")
                return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


@timed_cache(seconds=86400, maxsize=1)  # Cache for 24 hours
def fetch_currency_symbols() -> dict | None:
    """Get a JSON list of all currency symbols available from the Open Exchange Rates API."""
    logger.info("Fetching currency symbols")
    url = f"{base_url}currencies.json?app_id={app_id}&prettyprint=false&show_alternative=false&show_inactive=false"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error("Failed to decode JSON response for currency symbols")
            return None
    else:
        logger.error(
            f"Failed to fetch currency symbols. Status code: {response.status_code}"
        )
        return None


@timed_cache(seconds=3600)  # Cache for 1 hour
def fetch_exchange_rates(base_currency: str) -> dict | None:
    logger.info(f"Fetching exchange rates for base currency: {base_currency}")
    url = f"{base_url}latest.json?app_id={app_id}&base={base_currency}&prettyprint=false&show_alternative=false"

    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            exchange_rates = response.json()
            return exchange_rates["rates"]
        except requests.exceptions.JSONDecodeError:
            logger.error("Failed to decode JSON response for exchange rates")
            return None
    else:
        logger.error(
            f"Failed to fetch exchange rates. Status code: {response.status_code}"
        )
        return None
