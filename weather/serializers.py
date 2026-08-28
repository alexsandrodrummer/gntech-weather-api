"""Serializers for the weather REST API."""

from rest_framework import serializers

from weather.models import WeatherRecord


class WeatherRecordSerializer(serializers.ModelSerializer):
    """Serialize stored weather records as read-only data."""

    class Meta:
        model = WeatherRecord
        fields = (
            "id",
            "city",
            "country",
            "temperature",
            "feels_like",
            "humidity",
            "pressure",
            "weather_description",
            "wind_speed",
            "collected_at",
        )
        read_only_fields = fields


class WeatherCollectionSerializer(serializers.Serializer):
    """Validate input accepted by the weather collection endpoint."""

    city = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)

