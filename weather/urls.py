"""URL routes for the weather REST API."""

from django.urls import path

from weather.views import (
    WeatherCollectionView,
    WeatherRecordDetailView,
    WeatherRecordListView,
)

app_name = "weather"

urlpatterns = [
    path("", WeatherRecordListView.as_view(), name="record-list"),
    path("collect/", WeatherCollectionView.as_view(), name="collect"),
    path("<int:pk>/", WeatherRecordDetailView.as_view(), name="record-detail"),
]

