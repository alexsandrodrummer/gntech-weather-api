"""Tests for the weather REST endpoints."""

from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from weather.models import WeatherRecord
from weather.services.openweather import (
    CityNotFoundError,
    OpenWeatherResponseError,
    OpenWeatherTimeoutError,
)


class WeatherEndpointTests(APITestCase):
    """Verify list, detail, and collection API behavior."""

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

    def _create_record(self, **overrides):
        data = {**self.weather_data, **overrides}
        return WeatherRecord.objects.create(**data)

    def test_list_returns_weather_records(self):
        first = self._create_record(city="Campinas")
        second = self._create_record(city="Sao Paulo")

        response = self.client.get(reverse("weather:record-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            {item["id"] for item in response.data}, {first.pk, second.pk}
        )

    def test_list_returns_empty_array_without_records(self):
        response = self.client.get(reverse("weather:record-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_detail_returns_existing_weather_record(self):
        record = self._create_record()

        response = self.client.get(
            reverse("weather:record-detail", kwargs={"pk": record.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], record.pk)
        self.assertEqual(response.data["city"], "Campinas")

    def test_detail_returns_404_for_missing_record(self):
        response = self.client.get(
            reverse("weather:record-detail", kwargs={"pk": 9999})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("weather.services.weather_service.get_current_weather")
    def test_collect_returns_201_and_persists_record(self, mock_get_weather):
        mock_get_weather.return_value = self.weather_data

        response = self.client.post(
            reverse("weather:collect"), {"city": "Campinas"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["city"], "Campinas")
        self.assertTrue(WeatherRecord.objects.filter(pk=response.data["id"]).exists())
        mock_get_weather.assert_called_once_with("Campinas")

    @patch("weather.services.weather_service.get_current_weather")
    def test_collect_rejects_empty_city_without_external_call(self, mock_get_weather):
        response = self.client.post(
            reverse("weather:collect"), {"city": ""}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_get_weather.assert_not_called()

    @patch("weather.services.weather_service.get_current_weather")
    def test_collect_returns_404_for_unknown_city(self, mock_get_weather):
        mock_get_weather.side_effect = CityNotFoundError

        response = self.client.post(
            reverse("weather:collect"), {"city": "Unknown"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "City not found.")

    @patch("weather.services.weather_service.get_current_weather")
    def test_collect_returns_503_on_external_timeout(self, mock_get_weather):
        mock_get_weather.side_effect = OpenWeatherTimeoutError

        response = self.client.post(
            reverse("weather:collect"), {"city": "Campinas"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("weather.services.weather_service.get_current_weather")
    def test_collect_returns_502_on_invalid_external_response(self, mock_get_weather):
        mock_get_weather.side_effect = OpenWeatherResponseError

        response = self.client.post(
            reverse("weather:collect"), {"city": "Campinas"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
