from django.contrib import admin

from .models import HazardZone, MapLocation, SafeZone


@admin.register(MapLocation)
class MapLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "location_type", "latitude", "longitude", "is_active")
    search_fields = ("name", "description")
    list_filter = ("location_type", "is_active")


@admin.register(HazardZone)
class HazardZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "hazard_type", "risk_level", "latitude", "longitude")
    search_fields = ("name", "description")
    list_filter = ("hazard_type", "risk_level")


@admin.register(SafeZone)
class SafeZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude")
    search_fields = ("name", "description")
