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

    def get_queryset(self):
        name = self.request.query_params.get("name")
        closest_big_city = self.request.query_params.get("closest_big_city")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)

        if closest_big_city:
            queryset = queryset.filter(closest_big_city__icontains=closest_big_city)

        return queryset


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteRetrieveSerializer
        return RouteSerializer

    def get_queryset(self):
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")

        queryset = self.queryset

        if source:
            queryset = queryset.filter(source__id=source)

        if destination:
            queryset = queryset.filter(destination__id=destination)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("source", "destination")
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

    @staticmethod
    def _params_to_ints(query_string):
        """Converts a string of format '1, 2, 3' to a list of integers [1, 2, 3]."""
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer

    def get_queryset(self):
        route = self.request.query_params.get("route")
        airplane = self.request.query_params.get("airplane")
        departure_time = self.request.query_params.get("departure_time")
        arrival_time = self.request.query_params.get("arrival_time")
        crews = self.request.query_params.get("crews")

        queryset = self.queryset

        if route:
            queryset = queryset.filter(route__id=route)

        if airplane:
            queryset = queryset.filter(airplane__id=airplane)

        if departure_time:
            queryset = queryset.filter(departure_time__date=departure_time)

        if arrival_time:
            queryset = queryset.filter(arrival_time__date=arrival_time)

        if crews:
            crews = self._params_to_ints(crews)
            queryset = queryset.filter(crews__id__in=crews)

        if self.action in ("list", "retrieve"):
            queryset = (queryset.select_related("airplane", "route")
                        .prefetch_related("crews"))
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self):
        created = self.request.query_params.get("created")

        queryset = self.queryset.filter(user=self.request.user)

        if created:
            queryset = queryset.filter(created__date=created)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
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


