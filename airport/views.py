from django.db.models import Count, F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from airport.models import (Crew,
                            Airport,
                            Route,
                            AirplaneType,
                            Airplane,
                            Flight,
                            Order, City, Country, Airline)

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
                                 FlightRetrieveSerializer,
                                 OrderListSerializer,
                                 OrderRetrieveSerializer,
                                 CrewImageSerializer,
                                 AirplaneImageSerializer, CitySerializer, CountrySerializer, AirlineSerializer,
                                 CountryListSerializer)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

    def get_serializer_class(self):
        if self.action == "upload_image":
            return CrewImageSerializer
        return CrewSerializer

    @extend_schema(
        request=CrewImageSerializer,
        responses=CrewSerializer,
        description="Upload image for crew member",
    )
    @action(
        methods=["POST"],
        detail=True
    )
    def upload_image(self, request, pk=None):
        crew = self.get_object()
        serializer = self.get_serializer(crew, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by airport name (ex. ?name=boryspil)"
            ),
            OpenApiParameter(
                "closest_big_city",
                type=OpenApiTypes.STR,
                description="Filter by closest big city (ex. ?closest_big_city=kyiv)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "source",
                type=OpenApiTypes.INT,
                description="Filter by source (ex. ?source=1)"
            ),
            OpenApiParameter(
                "destination",
                type=OpenApiTypes.INT,
                description="Filter by destination (ex. ?destination=1)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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
        elif self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            return queryset.select_related("airplane_type")
        return queryset

    @extend_schema(
        request=AirplaneImageSerializer,
        responses=AirplaneSerializer,
        description="Upload image for airplane",
    )
    @action(
        methods=["POST"],
        detail=True
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        if self.action == "list":
            queryset = (queryset.select_related("airplane", "route", "airline")
                        .prefetch_related("crews")
                        .annotate(tickets_available=F("airplane__rows")
                                                    * F("airplane__seats_in_row")
                                                    - Count("tickets")))

        if self.action == "retrieve":
            queryset = (queryset.select_related("airplane", "route")
                        .prefetch_related("crews"))
        return queryset.distinct().order_by("id")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "route",
                type=OpenApiTypes.INT,
                description="Filter by route (ex. ?route=1)"
            ),
            OpenApiParameter(
                "airplane",
                type=OpenApiTypes.INT,
                description="Filter by airplane (ex. ?airplane=1)"
            ),
            OpenApiParameter(
                "departure_time",
                type=OpenApiTypes.DATE,
                description="Filter by departure time (ex. ?departure_time=2022-10-23)"
            ),
            OpenApiParameter(
                "arrival_time",
                type=OpenApiTypes.DATE,
                description="Filter by arrival time (ex. ?arrival_time=2022-10-23)"
            ),
            OpenApiParameter(
                "crews",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by crews (ex. ?crews=1,2)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "created",
                type=OpenApiTypes.DATE,
                description="Filter by created date (ex. created=2022-10-23)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("cities")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return CountryListSerializer
        return CountrySerializer


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer
