from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import City, Country, Airport
from airport.serializers import AirportSerializer

AIRPORT_URL = reverse("airport:airport-list")


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


def detail_url(airport_id):
    return reverse("airport:airport-detail", args=[airport_id])


class UnauthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(AIRPORT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_airports(self):
        sample_airport()
        sample_airport()

        res = self.client.get(AIRPORT_URL)

        airports = Airport.objects.order_by("id")
        serializer = AirportSerializer(airports, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_airports_by_name(self):
        airport1 = sample_airport(name="Airport")
        airport2 = sample_airport(name="Another Airport")
        airport3 = sample_airport(name="No match")

        res = self.client.get(AIRPORT_URL, {"name": "airport"})

        serializer1 = AirportSerializer(airport1)
        serializer2 = AirportSerializer(airport2)
        serializer3 = AirportSerializer(airport3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_filter_airports_by_closest_big_city(self):
        city1 = sample_city(name="City")
        city2 = sample_city(name="No match")

        airport1 = sample_airport(closest_big_city=city1)
        airport2 = sample_airport(closest_big_city=city1)
        airport3 = sample_airport(closest_big_city=city2)

        res = self.client.get(AIRPORT_URL, {"closest_big_city": f"{city1.id}"})

        serializer1 = AirportSerializer(airport1)
        serializer2 = AirportSerializer(airport2)
        serializer3 = AirportSerializer(airport3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_airport_detail(self):
        airport = sample_airport()

        url = detail_url(airport.id)
        res = self.client.get(url)

        serializer = AirportSerializer(airport)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airport_forbidden(self):
        payload = {
            "name": "Airport",
            "closest_big_city": sample_city(),
        }
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airport(self):
        city = sample_city()
        payload = {
            "name": "Airport",
            "closest_big_city": city.id,
        }
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        airport = Airport.objects.get(id=res.data["id"])

        self.assertEqual(airport.name, payload["name"])
        self.assertEqual(airport.closest_big_city, city)
