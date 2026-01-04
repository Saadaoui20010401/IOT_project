from django.contrib import admin
from .models import Dht11, Incident, OperatorProfile


@admin.register(Dht11)
class Dht11Admin(admin.ModelAdmin):
    list_display = ("dt", "temp", "hum")
    ordering = ("-dt",)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "incident_type",
        "start_at",
        "end_at",
        "max_temp",
        "counter",
        "is_open",
    )
    list_filter = ("incident_type", "is_open")
    search_fields = ("id",)
    ordering = ("-start_at",)


@admin.register(OperatorProfile)
class OperatorProfileAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "email", "phone", "user")
    search_fields = ("prenom", "nom", "email", "user__username")
