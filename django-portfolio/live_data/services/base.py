import requests
from requests.exceptions import RequestException


class APIServiceError(Exception):
    """Custom exception for API failures"""
    pass


def safe_get(url, params=None, timeout=5):
    """
    Safe GET request wrapper with timeout and error handling.
    Prevents hanging EC2 workers.
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        raise APIServiceError(f"API request failed: {str(e)}")
