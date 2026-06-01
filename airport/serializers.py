from django.db import transaction

from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from airport.models import Crew, Airport, Route, AirplaneType, Airplane, Flight, Order, Ticket, City, Country, Airline


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "image")
        read_only_fields = ("image",)


class CrewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "image")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source_airport", "destination_airport", "distance")

    source_airport = serializers.CharField(source="source.name", read_only=True)
    destination_airport = serializers.CharField(source="destination.name", read_only=True)


class RouteRetrieveSerializer(RouteSerializer):
    source = AirportSerializer(many=False, read_only=True)
    destination = AirportSerializer(many=False, read_only=True)



class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type", "image")
        read_only_fields = ("image",)


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image")


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.CharField(source="airplane_type.name", read_only=True)


class AirplaneRetrieveSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(many=False, read_only=True)


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ("id", "name")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "airline", "departure_time", "arrival_time", "crews")


class FlightListSerializer(serializers.ModelSerializer):
    route = serializers.StringRelatedField(many=False, read_only=True)
    airplane = serializers.CharField(source="airplane.name", read_only=True)
    crews = serializers.StringRelatedField(many=True, read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)
    airline = SlugRelatedField(many=False, read_only=True, slug_field="name")

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "airline", "departure_time",
                  "arrival_time", "crews", "tickets_available")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")

    def validate(self, attrs):
        Ticket.validate_seat_and_row(attrs["seat"],
                                     attrs["flight"].airplane.seats_in_row,
                                     attrs["row"],
                                     attrs["flight"].airplane.rows,
                                     serializers.ValidationError)
        return attrs


class FlightRetrieveSerializer(FlightSerializer):
    route = RouteRetrieveSerializer(many=False, read_only=True)
    airplane = AirplaneRetrieveSerializer(many=False, read_only=True)
    crews = CrewSerializer(many=True, read_only=True)
    tickets = serializers.StringRelatedField(many=True, read_only=True)
    airline = AirlineSerializer(many=False, read_only=True)

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "airline", "departure_time", "arrival_time", "crews", "tickets")


class TicketRetrieveSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = serializers.StringRelatedField(many=True, read_only=True, allow_empty=False)


class OrderRetrieveSerializer(OrderSerializer):
    tickets = TicketRetrieveSerializer(many=True, read_only=True, allow_empty=False)


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name", "cities")

    cities = CitySerializer(many=True, read_only=False, allow_empty=False)

    def create(self, validated_data):
        with transaction.atomic():
            cities_data = validated_data.pop("cities")
            country = Country.objects.create(**validated_data)
            for city_data in cities_data:
                City.objects.create(country=country, **city_data)
            return country


class CountryListSerializer(CountrySerializer):
    cities = SlugRelatedField(many=True, read_only=True, slug_field="name")\
