from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from airport.models import Country
from airport.serializers import CountryListSerializer

COUNTRY_URL = reverse("airport:country-list")


def sample_country(**params):
    defaults = {
        "name": "Country",
    }
    defaults.update(params)
    return Country.objects.create(**defaults)


class UnauthenticatedCountryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(COUNTRY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_movies(self):
        sample_country()
        sample_country()

        res = self.client.get(COUNTRY_URL)

        countries = Country.objects.order_by("id")
        serializer = CountryListSerializer(countries, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_country_forbidden(self):
        payload = {
            "name": "Country"
        }
        res = self.client.post(COUNTRY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCountryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_order(self):
        payload = {
            "name": "Country",
            "cities": [
                {"name": "City"}
            ]
        }
        res = self.client.post(COUNTRY_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        country = Country.objects.get(id=res.data["id"])

        self.assertEqual(country.cities.count(), 1)

        city = country.cities.first()
        self.assertEqual(city.name, payload["cities"][0]["name"])
