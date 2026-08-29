from django.db import models

# Create your models here.
from django.db import models


class WeatherRecord(models.Model):
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=10)

    temperature = models.FloatField()
    feels_like = models.FloatField()

    humidity = models.PositiveIntegerField()
    pressure = models.PositiveIntegerField()

    weather_description = models.CharField(max_length=255)
    wind_speed = models.FloatField()

    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-collected_at"]

    def __str__(self):
        return f"{self.city} - {self.temperature}°C"