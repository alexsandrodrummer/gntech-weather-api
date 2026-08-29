"""Tests for the OpenWeather HTTP client."""

import os
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase

from weather.services.openweather import (
    CityNotFoundError,
    InvalidAPIKeyError,
    InvalidCityError,
    OpenWeatherConfigurationError,
    OpenWeatherConnectionError,
    OpenWeatherResponseError,
    OpenWeatherTimeoutError,
    get_current_weather,
)


class GetCurrentWeatherTests(SimpleTestCase):
    """Exercise successful and failed responses from OpenWeather."""

    valid_payload = {
        "name": "Campinas",
        "sys": {"country": "BR"},
        "main": {
            "temp": 24.5,
            "feels_like": 25.1,
            "humidity": 70,
            "pressure": 1015,
        },
        "weather": [{"description": "clear sky"}],
        "wind": {"speed": 3.2},
    }

    def _response(self, status_code=200, payload=None):
        response = Mock(status_code=status_code)
        response.json.return_value = self.valid_payload if payload is None else payload
        return response

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_returns_normalized_weather_data_on_success(self, mock_get):
        mock_get.return_value = self._response()

        result = get_current_weather("  Campinas  ")

        self.assertEqual(
            result,
            {
                "city": "Campinas",
                "country": "BR",
                "temperature": 24.5,
                "feels_like": 25.1,
                "humidity": 70,
                "pressure": 1015,
                "weather_description": "clear sky",
                "wind_speed": 3.2,
            },
        )
        mock_get.assert_called_once_with(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": "Campinas",
                "appid": "test-api-key",
                "units": "metric",
            },
            timeout=10,
        )

    @patch("weather.services.openweather.requests.get")
    def test_rejects_empty_city_without_making_request(self, mock_get):
        for city in ("", "   "):
            with self.subTest(city=repr(city)):
                with self.assertRaises(InvalidCityError):
                    get_current_weather(city)

        mock_get.assert_not_called()

    @patch("weather.services.openweather.requests.get")
    def test_rejects_missing_api_key_without_making_request(self, mock_get):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(OpenWeatherConfigurationError):
                get_current_weather("Campinas")

        mock_get.assert_not_called()

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_translates_request_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout

        with self.assertRaises(OpenWeatherTimeoutError):
            get_current_weather("Campinas")

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_translates_connection_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError

        with self.assertRaises(OpenWeatherConnectionError):
            get_current_weather("Campinas")

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_raises_city_not_found_for_404(self, mock_get):
        mock_get.return_value = self._response(status_code=404)

        with self.assertRaises(CityNotFoundError):
            get_current_weather("Unknown")

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_raises_invalid_api_key_for_unauthorized_response(self, mock_get):
        for status_code in (401, 403):
            with self.subTest(status_code=status_code):
                mock_get.return_value = self._response(status_code=status_code)
                with self.assertRaises(InvalidAPIKeyError):
                    get_current_weather("Campinas")

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_rejects_unexpected_http_status(self, mock_get):
        mock_get.return_value = self._response(status_code=500)

        with self.assertRaises(OpenWeatherResponseError):
            get_current_weather("Campinas")

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_rejects_invalid_json(self, mock_get):
        response = self._response()
        response.json.side_effect = ValueError("invalid JSON")
        mock_get.return_value = response

        with self.assertRaises(OpenWeatherResponseError):
            get_current_weather("Campinas")

    @patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-api-key"})
    @patch("weather.services.openweather.requests.get")
    def test_rejects_incomplete_response(self, mock_get):
        mock_get.return_value = self._response(payload={"name": "Campinas"})

        with self.assertRaises(OpenWeatherResponseError):
            get_current_weather("Campinas")
