from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import AirplaneType, Airplane, City, Airport, Route, Country, Airline, Flight, Crew
from airport.serializers import FlightListSerializer, FlightRetrieveSerializer

FLIGHT_URL = reverse("airport:flight-list")


def sample_crew(**params):
    defaults = {
        "first_name": "test_first_name",
        "last_name": "test_last_name",
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_airplane_type(**params):
    defaults = {
        "name": "Airplane Type",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params):
    defaults = {
        "name": "Airplane",
        "rows": 20,
        "seats_in_row": 2,
        "airplane_type": sample_airplane_type(),
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_country(**params):
    defaults = {
        "name": "Country"
    }
    defaults.update(params)
    return Country.objects.create(**defaults)


def sample_city(**params):
    defaults = {
        "name": "City",
        "country": sample_country()
    }
    defaults.update(params)
    return City.objects.create(**defaults)


def sample_airport(**params):
    defaults = {
        "name": "Sample Airport",
        "closest_big_city": sample_city(),
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_route(**params):
    defaults = {
        "source": sample_airport(name="Source Airport"),
        "destination": sample_airport(name="Destination Airport"),
        "distance": 100,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_airline(**params):
    defaults = {
        "name": "Sample Airline",
    }
    defaults.update(params)
    return Airline.objects.create(**defaults)


def sample_flight(**params):
    defaults = {
        "route": sample_route(),
        "airplane": sample_airplane(),
        "airline": sample_airline(),
        "departure_time": timezone.now(),
        "arrival_time": timezone.now() + timezone.timedelta(hours=2),
    }
    defaults.update(params)
    return Flight.objects.create(**defaults)


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(FLIGHT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_flights(self):
        sample_flight()
        sample_flight()
        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.annotate(
            tickets_available=F("airplane__rows")
                              * F("airplane__seats_in_row")
                              - Count("tickets")).order_by("id")

        serializer = FlightListSerializer(flights, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_flights_by_route(self):
        route1 = sample_route(distance=500)
        route2 = sample_route(distance=1000)

        flight1 = sample_flight(route=route1)
        flight2 = sample_flight(route=route1)
        flight3 = sample_flight(route=route2)

        res = self.client.get(
            FLIGHT_URL, {"route": route1.id}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight1.id, flight_ids)
        self.assertIn(flight2.id, flight_ids)
        self.assertNotIn(flight3.id, flight_ids)

    def test_filter_flights_by_airplane(self):
        airplane1 = sample_airplane(name="Airplane1")
        airplane2 = sample_airplane(name="Airplane2")

        flight1 = sample_flight(airplane=airplane1)
        flight2 = sample_flight(airplane=airplane1)
        flight3 = sample_flight(airplane=airplane2)

        res = self.client.get(
            FLIGHT_URL, {"airplane": airplane1.id}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight1.id, flight_ids)
        self.assertIn(flight2.id, flight_ids)
        self.assertNotIn(flight3.id, flight_ids)

    def test_filter_flights_by_departure_time(self):
        flight1 = sample_flight(departure_time="2025-05-30")
        flight2 = sample_flight(departure_time="2025-05-31")

        res = self.client.get(
            FLIGHT_URL, {"departure_time": "2025-05-30"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight1.id, flight_ids)
        self.assertNotIn(flight2.id, flight_ids)

    def test_filter_flights_by_arrival_time(self):
        flight1 = sample_flight(arrival_time="2025-05-30")
        flight2 = sample_flight(arrival_time="2025-05-31")

        res = self.client.get(
            FLIGHT_URL, {"arrival_time": "2025-05-30"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight1.id, flight_ids)
        self.assertNotIn(flight2.id, flight_ids)

    def test_filter_flights_by_crews(self):
        crew1 = sample_crew(first_name="first_name1", last_name="last_name1")
        crew2 = sample_crew(first_name="first_name2", last_name="last_name2")

        flight1 = sample_flight(departure_time="2025-05-30")
        flight2 = sample_flight(departure_time="2025-05-31")

        flight1.crews.add(crew1)
        flight2.crews.add(crew2)

        flight3 = sample_flight()

        res = self.client.get(
            FLIGHT_URL, {"crews": f"{crew1.id},{crew2.id}"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight1.id, flight_ids)
        self.assertIn(flight2.id, flight_ids)
        self.assertNotIn(flight3.id, flight_ids)

    def test_retrieve_flight_detail(self):
        flight = sample_flight()
        flight.crews.add(sample_crew())

        url = detail_url(flight.id)
        res = self.client.get(url)

        serializer = FlightRetrieveSerializer(flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_forbidden(self):
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "airline": sample_airline().id,
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timezone.timedelta(hours=2),
        }
        res = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_flight(self):
        route = sample_route()
        airplane = sample_airplane()
        airline = sample_airline()
        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "airline": airline.id,
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timezone.timedelta(hours=2),
        }
        res = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        flight = Flight.objects.get(id=res.data["id"])
        self.assertEqual(flight.route, route)
        self.assertEqual(flight.airplane, airplane)
        self.assertEqual(flight.airline, airline)

    def test_create_flight_with_crews(self):
        crew1 = sample_crew(first_name="first_name1", last_name="last_name1")
        crew2 = sample_crew(first_name="first_name2", last_name="last_name2")
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "airline": sample_airline().id,
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timezone.timedelta(hours=2),
            "crews": [crew1.id, crew2.id],
        }
        res = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        flight = Flight.objects.get(id=res.data["id"])
        crews = flight.crews.all()
        self.assertEqual(crews.count(), 2)
        self.assertIn(crew1, crews)
        self.assertIn(crew2, crews)
