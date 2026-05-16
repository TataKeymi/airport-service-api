from django.contrib.auth.models import User
from django.db import models
from django.db.models import ForeignKey, ManyToManyField
from django.conf import settings


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Airport(models.Model):
    name = models.CharField(max_length=100)
    closest_big_city = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Route(models.Model):
    source = ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="departure_routes",
    )
    destination = ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="arrival_routes",
    )
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source} -> {self.destination}"


class AirplaneType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Airplane(models.Model):
    name = models.CharField(max_length=100)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes"
    )

    def __str__(self):
        return f"{self.name} ({self.rows}, {self.seats_in_row})"


class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights")
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crews = ManyToManyField(Crew)

    def __str__(self):
        return f"Flight by route: {self.route}"


class Order(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    def __str__(self):
        return f"Order of: {self.user}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        unique_together = ("row", "seat", "flight")

    def __str__(self):
        return f"Ticket of: {self.order}, row: {self.row}, seat: {self.seat}, flight: {self.flight}"
