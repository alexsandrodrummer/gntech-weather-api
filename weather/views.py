from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
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


ErrorResponseSerializer = inline_serializer(
    name="ErrorResponse",
    fields={"detail": serializers.CharField()},
)


class WeatherCollectionView(APIView):
    """Collect and persist current weather data for a city."""

    @extend_schema(
        summary="Collect current weather",
        description=(
            "Collects current weather data for the requested city and stores "
            "the resulting record."
        ),
        request=WeatherCollectionSerializer,
        responses={
            201: WeatherRecordSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid request or empty city.",
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="City not found.",
            ),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid response from the external weather service.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="External weather service unavailable.",
            ),
        },
        examples=[
            OpenApiExample(
                "City request",
                value={"city": "Campinas"},
                request_only=True,
            )
        ],
        tags=["Weather"],
    )
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

    @extend_schema(
        summary="List weather records",
        description="Returns all stored weather records in model-defined order.",
        responses={200: WeatherRecordSerializer(many=True)},
        tags=["Weather"],
    )
    def get(self, request: Request) -> Response:
        weather_records = WeatherRecord.objects.all()
        serializer = WeatherRecordSerializer(weather_records, many=True)
        return Response(serializer.data)


class WeatherRecordDetailView(APIView):
    """Retrieve one stored weather record."""

    @extend_schema(
        summary="Retrieve a weather record",
        description="Returns a stored weather record by its ID.",
        responses={
            200: WeatherRecordSerializer,
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Weather record not found.",
            ),
        },
        tags=["Weather"],
    )
    def get(self, request: Request, pk: int) -> Response:
        weather_record = get_object_or_404(WeatherRecord, pk=pk)
        serializer = WeatherRecordSerializer(weather_record)
        return Response(serializer.data)
