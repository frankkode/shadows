# models.py
from django.db import models

class ParkingOccupancy(models.Model):
    timestamp = models.DateTimeField()
    lot_number = models.IntegerField()
    is_occupied = models.BooleanField()

class TemperatureData(models.Model):
    timestamp = models.DateTimeField()
    temperature = models.FloatField()

