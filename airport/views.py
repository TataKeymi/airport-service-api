from rest_framework import viewsets

from airport.models import (Crew,
                            Airport,
                            Route,
                            AirplaneType,
                            Airplane,
                            Flight,
                            Order,
                            Ticket)

from airport.serializers import (CrewSerializer,
                                 AirportSerializer,
                                 RouteSerializer,
                                 AirplaneTypeSerializer,
                                 AirplaneSerializer,
                                 FlightSerializer,
                                 OrderSerializer,
                                 TicketSerializer, RouteListSerializer, RouteRetrieveSerializer, AirplaneListSerializer,
                                 AirplaneRetrieveSerializer, FlightListSerializer, FlightRetrieveSerializer,
                                 TicketListSerializer, TicketRetrieveSerializer)


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
    serializer_class = OrderSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        elif self.action == "retrieve":
            return TicketRetrieveSerializer
        return TicketSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = self.queryset.select_related("flight", "order")
        return queryset
