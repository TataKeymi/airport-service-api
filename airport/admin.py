from django.contrib import admin

from airport.models import (Crew,
                            Airport,
                            Route,
                            AirplaneType,
                            Airplane,
                            Flight,
                            Order,
                            Ticket,
                            City,
                            Country,
                            Airline)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInline, )


class CityInline(admin.TabularInline):
    model = City
    extra = 1


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    inlines = (CityInline, )


admin.site.register(Crew)
admin.site.register(Airport)
admin.site.register(Route)
admin.site.register(AirplaneType)
admin.site.register(Airplane)
admin.site.register(Flight)
admin.site.register(Ticket)
admin.site.register(City)
admin.site.register(Airline)
