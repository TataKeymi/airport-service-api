import datetime
from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Order, Flight, Airline, Route, Airport, City, Country, Airplane, AirplaneType
from airport.serializers import OrderListSerializer, OrderRetrieveSerializer

ORDER_URL = reverse("airport:order-list")


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


def sample_order(**params):
    user = params.pop("user", None) or get_user_model().objects.create(
        "test@test.com",
        "testpass",
    )
    defaults = {
        "created": timezone.now(),
        "user": user,
    }
    defaults.update(params)
    return Order.objects.create(**defaults)


def set_order_created(order, date_string):
    created = timezone.make_aware(
        datetime.fromisoformat(date_string + "T12:00:00")
    )
    Order.objects.filter(id=order.id).update(created=created)
    order.refresh_from_db()
    return order


def detail_url(order_id):
    return reverse("airport:order-detail", args=[order_id])


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_orders(self):
        sample_order(user=self.user)
        sample_order(user=self.user)

        res = self.client.get(ORDER_URL)

        orders = Order.objects.filter(user=self.user).order_by("-created")
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_orders_by_created(self):
        order1 = sample_order(user=self.user)
        order2 = sample_order(user=self.user)

        order1 = set_order_created(order1, "2025-05-30")
        order2 = set_order_created(order2, "2025-05-31")

        res = self.client.get(
            ORDER_URL, {"created": "2025-05-30"}
        )

        serializer1 = OrderListSerializer(order1)
        serializer2 = OrderListSerializer(order2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_order_list_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            "test2@test2.com",
            "testpass2",
        )
        order1 = sample_order(user=self.user)
        order2 = sample_order(user=user2)

        res = self.client.get(ORDER_URL)

        serializer1 = OrderListSerializer(order1)
        serializer2 = OrderListSerializer(order2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_order_detail(self):
        order = sample_order(user=self.user)

        url = detail_url(order.id)
        res = self.client.get(url)

        serializer = OrderRetrieveSerializer(order)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_order_forbidden(self):
        payload = {}
        res = self.client.post(ORDER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_order(self):
        flight = sample_flight()
        payload = {
            "tickets": [
                {
                    "row": 1,
                    "seat": 1,
                    "flight": flight.id,
                }
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.tickets.count(), 1)

        ticket = order.tickets.first()
        self.assertEqual(ticket.row, 1)
        self.assertEqual(ticket.seat, 1)
        self.assertEqual(ticket.flight, flight)
