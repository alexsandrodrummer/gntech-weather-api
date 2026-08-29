"""Tests for weather collection and persistence."""

from unittest.mock import patch

from django.test import TestCase

from weather.models import WeatherRecord
from weather.services.weather_service import collect_weather


class CollectWeatherTests(TestCase):
    """Verify that normalized external data is stored correctly."""

    @patch("weather.services.weather_service.get_current_weather")
    def test_collects_and_persists_returned_weather_data(self, mock_get_weather):
        weather_data = {
            "city": "Campinas",
            "country": "BR",
            "temperature": 24.5,
            "feels_like": 25.1,
            "humidity": 70,
            "pressure": 1015,
            "weather_description": "clear sky",
            "wind_speed": 3.2,
        }
        mock_get_weather.return_value = weather_data

        record = collect_weather("  Campinas  ")

        mock_get_weather.assert_called_once_with("Campinas")
        self.assertEqual(WeatherRecord.objects.count(), 1)
        persisted_record = WeatherRecord.objects.get(pk=record.pk)
        for field, expected_value in weather_data.items():
            with self.subTest(field=field):
                self.assertEqual(getattr(persisted_record, field), expected_value)
