from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from weather.models import WeatherRecord
from weather.serializers import WeatherCollectionSerializer, WeatherRecordSerializer
from weather.services.openweather import (
    CityNotFoundError,
    InvalidAPIKeyError,
    InvalidCityError,
    OpenWeatherConfigurationError,
    OpenWeatherConnectionError,
    OpenWeatherResponseError,
    OpenWeatherTimeoutError,
)
from weather.services.weather_service import collect_weather


class WeatherCollectionView(APIView):
    """Collect and persist current weather data for a city."""

    def post(self, request: Request) -> Response:
        input_serializer = WeatherCollectionSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            weather_record = collect_weather(input_serializer.validated_data["city"])
        except InvalidCityError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        except CityNotFoundError:
            return Response(
                {"detail": "City not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except (OpenWeatherConfigurationError, InvalidAPIKeyError):
            return Response(
                {"detail": "Weather service is unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except (OpenWeatherTimeoutError, OpenWeatherConnectionError):
            return Response(
                {"detail": "Weather service is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except OpenWeatherResponseError:
            return Response(
                {"detail": "Weather service returned an invalid response."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        output_serializer = WeatherRecordSerializer(weather_record)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class WeatherRecordListView(APIView):
    """List all stored weather records."""

    def get(self, request: Request) -> Response:
        weather_records = WeatherRecord.objects.all()
        serializer = WeatherRecordSerializer(weather_records, many=True)
        return Response(serializer.data)


class WeatherRecordDetailView(APIView):
    """Retrieve one stored weather record."""

    def get(self, request: Request, pk: int) -> Response:
        weather_record = get_object_or_404(WeatherRecord, pk=pk)
        serializer = WeatherRecordSerializer(weather_record)
        return Response(serializer.data)
