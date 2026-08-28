"""Client for the OpenWeather Current Weather API."""

import logging
import os
from typing import Any, TypedDict

import requests

logger = logging.getLogger(__name__)

OPENWEATHER_CURRENT_WEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)
REQUEST_TIMEOUT_SECONDS = 10


class WeatherData(TypedDict):
    """Normalized weather data expected by ``WeatherRecord``."""

    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    weather_description: str
    wind_speed: float


class OpenWeatherError(Exception):
    """Base exception for failures while consulting OpenWeather."""


class OpenWeatherConfigurationError(OpenWeatherError):
    """Raised when the OpenWeather client is not configured correctly."""


class InvalidCityError(OpenWeatherError):
    """Raised when no valid city is supplied."""


class CityNotFoundError(OpenWeatherError):
    """Raised when OpenWeather cannot find the requested city."""


class InvalidAPIKeyError(OpenWeatherError):
    """Raised when OpenWeather rejects the configured API key."""


class OpenWeatherTimeoutError(OpenWeatherError):
    """Raised when OpenWeather does not respond within the timeout."""


class OpenWeatherConnectionError(OpenWeatherError):
    """Raised when a connection with OpenWeather cannot be established."""


class OpenWeatherResponseError(OpenWeatherError):
    """Raised when OpenWeather returns an invalid or unexpected response."""


def get_current_weather(city: str) -> WeatherData:
    """Fetch and normalize the current weather for a city."""
    if not isinstance(city, str) or not city.strip():
        raise InvalidCityError("City must be a non-empty string.")

    normalized_city = city.strip()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or not api_key.strip():
        logger.error("OPENWEATHER_API_KEY is not configured")
        raise OpenWeatherConfigurationError(
            "OPENWEATHER_API_KEY is not configured."
        )

    try:
        response = requests.get(
            OPENWEATHER_CURRENT_WEATHER_URL,
            params={
                "q": normalized_city,
                "appid": api_key,
                "units": "metric",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.Timeout as exc:
        logger.warning("OpenWeather request timed out for city %r", normalized_city)
        raise OpenWeatherTimeoutError(
            "OpenWeather did not respond in time."
        ) from exc
    except requests.ConnectionError as exc:
        logger.error(
            "Could not connect to OpenWeather for city %r", normalized_city
        )
        raise OpenWeatherConnectionError(
            "Could not connect to OpenWeather."
        ) from exc
    except requests.RequestException as exc:
        logger.error("OpenWeather request failed for city %r", normalized_city)
        raise OpenWeatherConnectionError("OpenWeather request failed.") from exc

    if response.status_code == 404:
        raise CityNotFoundError(f"City {normalized_city!r} was not found.")
    if response.status_code in {401, 403}:
        logger.error("OpenWeather rejected the configured API key")
        raise InvalidAPIKeyError("OpenWeather rejected the configured API key.")
    if not 200 <= response.status_code < 300:
        logger.error(
            "Unexpected OpenWeather HTTP status %s for city %r",
            response.status_code,
            normalized_city,
        )
        raise OpenWeatherResponseError(
            f"OpenWeather returned unexpected HTTP status {response.status_code}."
        )

    try:
        payload = response.json()
    except (requests.exceptions.JSONDecodeError, ValueError) as exc:
        logger.error("OpenWeather returned invalid JSON for city %r", normalized_city)
        raise OpenWeatherResponseError(
            "OpenWeather returned an invalid JSON response."
        ) from exc

    try:
        return _normalize_weather_data(payload)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.error(
            "OpenWeather response is missing required data for city %r",
            normalized_city,
        )
        raise OpenWeatherResponseError(
            "OpenWeather response is missing required weather data."
        ) from exc


def _normalize_weather_data(payload: Any) -> WeatherData:
    if not isinstance(payload, dict):
        raise TypeError("Response payload must be an object.")

    weather_items = payload["weather"]
    if not isinstance(weather_items, list) or not weather_items:
        raise ValueError("Weather details are missing.")

    main = payload["main"]
    wind = payload["wind"]
    system = payload["sys"]

    city = _required_string(payload["name"])
    country = _required_string(system["country"])
    description = _required_string(weather_items[0]["description"])

    return {
        "city": city,
        "country": country,
        "temperature": _required_float(main["temp"]),
        "feels_like": _required_float(main["feels_like"]),
        "humidity": _required_int(main["humidity"]),
        "pressure": _required_int(main["pressure"]),
        "weather_description": description,
        "wind_speed": _required_float(wind["speed"]),
    }


def _required_string(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected a non-empty string.")
    return value.strip()


def _required_float(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Expected a number.")
    return float(value)


def _required_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Expected an integer.")
    return value
