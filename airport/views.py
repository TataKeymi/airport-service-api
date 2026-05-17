from rest_framework import viewsets

from airport.models import (Crew,
                            Airport,
                            Route,
                            AirplaneType,
                            Airplane,
                            Flight,
                            Order)

from airport.serializers import (CrewSerializer,
                                 AirportSerializer,
                                 RouteSerializer,
                                 AirplaneTypeSerializer,
                                 AirplaneSerializer,
                                 FlightSerializer,
                                 OrderSerializer,
                                 RouteListSerializer,
                                 RouteRetrieveSerializer,
                                 AirplaneListSerializer,
                                 AirplaneRetrieveSerializer,
                                 FlightListSerializer,
                                 FlightRetrieveSerializer, OrderListSerializer, OrderRetrieveSerializer)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteRetrieveSerializer
        return RouteSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = self.queryset.select_related("source", "destination")
        return queryset

class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        elif self.action == "retrieve":
            return AirplaneRetrieveSerializer
        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            return queryset.select_related("airplane_type")
        return queryset


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = (self.queryset.select_related("airplane", "route")
                        .prefetch_related("crews"))
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action in ("list", "retrieve"):
            queryset.prefetch_related(
                "tickets__flight",
                "tickets__flight__route",
                "tickets__flight__airplane")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderRetrieveSerializer
        return OrderSerializer


    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


