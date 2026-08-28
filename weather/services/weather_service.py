"""Application service for collecting and storing weather data."""

import logging

from weather.models import WeatherRecord
from weather.services.openweather import InvalidCityError, get_current_weather

logger = logging.getLogger(__name__)


def collect_weather(city: str) -> WeatherRecord:
    """Collect the current weather for a city and persist it."""
    if not isinstance(city, str) or not city.strip():
        raise InvalidCityError("City must be a non-empty string.")

    normalized_city = city.strip()
    weather_data = get_current_weather(normalized_city)
    weather_record = WeatherRecord.objects.create(**weather_data)

    logger.info("Weather collected successfully for city %r", normalized_city)
    return weather_record
