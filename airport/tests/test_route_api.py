from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Country, City, Airport, Route
from airport.serializers import RouteListSerializer, RouteRetrieveSerializer

ROUTE_URL =reverse("airport:route-list")


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


def detail_url(route_id):
    return reverse("airport:route-detail", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_routes(self):
        sample_route()
        sample_route()

        res = self.client.get(ROUTE_URL)

        routes = Route.objects.order_by("id")
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_routes_by_source(self):
        source1 = sample_airport(name="Source1")
        source2 = sample_airport(name="Source2")

        route1 = sample_route(source=source1)
        route2 = sample_route(source=source1)
        route3 = sample_route(source=source2)

        res = self.client.get(
            ROUTE_URL, {"source": source1.id}
        )

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)
        serializer3 = RouteListSerializer(route3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_filter_routes_by_destination(self):
        destination1 = sample_airport(name="Destination1")
        destination2 = sample_airport(name="Destination2")

        route1 = sample_route(destination=destination1)
        route2 = sample_route(destination=destination1)
        route3 = sample_route(destination=destination2)

        res = self.client.get(
            ROUTE_URL, {"destination": destination1.id}
        )

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)
        serializer3 = RouteListSerializer(route3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_route_detail(self):
        route = sample_route()
        res = self.client.get(detail_url(route.id))
        serializer = RouteRetrieveSerializer(route)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        payload = {
            "source": sample_airport(name="Source Airport"),
            "destination": sample_airport(name="Destination Airport"),
            "distance": 100,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        source = sample_airport(name="Source Airport")
        destination = sample_airport(name="Destination Airport")
        payload = {
            "source": source.id,
            "destination": destination.id,
            "distance": 100,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        route = Route.objects.get(id=res.data["id"])
        self.assertEqual(route.source, source)
        self.assertEqual(route.destination, destination)
        self.assertEqual(route.distance, payload["distance"])
