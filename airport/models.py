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
        ordering = ("seat",)

    def __str__(self):
        return f"Ticket's row: {self.row}, seat: {self.seat}, flight: {self.flight}"

    @staticmethod
    def validate_seat_and_row(seat: int, num_seats: int,
                              row: int, num_rows: int, error_to_raise):
        if not (1 <= seat <= num_seats):
            raise error_to_raise(
                {
                "seat": f"seat must be in range [1, {num_seats}], not {seat}"
                }
            )
        elif not (1 <= row <= num_rows):
            raise error_to_raise(
                {
                    "row": f"row must be in range [1, {num_rows}], not {row}"
                }
            )

    def clean(self):
        Ticket.validate_seat_and_row(self.seat, self.flight.airplane.seats_in_row,
                                     self.row, self.flight.airplane.rows,
                                     ValueError)

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None):
        self.full_clean()
        return super(Ticket, self).save(force_insert=force_insert,
                                        force_update=force_update,
                                        using=using,
                                        update_fields=update_fields)
