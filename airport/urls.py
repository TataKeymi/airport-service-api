from django.urls import include, path
from rest_framework import routers

from airport.views import (CrewViewSet,
                           AirportViewSet,
                           RouteViewSet,
                           AirplaneTypeViewSet,
                           AirplaneViewSet, FlightViewSet, OrderViewSet)


app_name = "airport"

router = routers.DefaultRouter()

router.register("crews", CrewViewSet)
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
