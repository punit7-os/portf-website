from django.core.cache import cache
from .base import safe_get, APIServiceError


class WeatherService:

    CACHE_KEY = "live_weather_data"
    CACHE_TIMEOUT = 60  # 1 minute (aligned refresh)

    @staticmethod
    def get_current_weather(latitude=19.0760, longitude=72.8777):

        cached_data = cache.get(WeatherService.CACHE_KEY)
        if cached_data:
            return cached_data

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "wind_speed_10m",
                "rain"
            ]
        }

        try:
            data = safe_get(url, params=params)

            current = data.get("current", {})

            weather_data = {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind": current.get("wind_speed_10m"),
                "rain": current.get("rain"),
            }

            cache.set(
                WeatherService.CACHE_KEY,
                weather_data,
                WeatherService.CACHE_TIMEOUT
            )

            return weather_data

        except APIServiceError:
            return {
                "error": "Unable to fetch weather data at the moment."
            }
