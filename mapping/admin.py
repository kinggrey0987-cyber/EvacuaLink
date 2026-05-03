from django.contrib import admin
from django.utils.html import format_html

from .models import HazardZone, MapLocation, SafeZone


@admin.register(MapLocation)
class MapLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "location_type", "get_coordinates", "get_active_badge")
    search_fields = ("name", "description")
    list_filter = ("location_type", "is_active")
    readonly_fields = ("coordinates_display",)
    ordering = ("name",)

    fieldsets = (
        ("Location Information", {
            "fields": ("name", "location_type", "description", "is_active")
        }),
        ("Geographic Data", {
            "fields": ("latitude", "longitude", "coordinates_display")
        }),
    )

    @admin.display(description="Coordinates")
    def get_coordinates(self, obj):
        return f"{obj.latitude:.4f}, {obj.longitude:.4f}"

    @admin.display(description="Coordinates")
    def coordinates_display(self, obj):
        return f"Latitude: {obj.latitude}, Longitude: {obj.longitude}"

    @admin.display(description="Status", ordering="is_active")
    def get_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 4px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 4px;">Inactive</span>'
        )


@admin.register(HazardZone)
class HazardZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "hazard_type", "get_risk_level_badge", "get_coordinates", "description_preview")
    search_fields = ("name", "description")
    list_filter = ("hazard_type", "risk_level")
    readonly_fields = ("coordinates_display",)
    ordering = ("name",)

    fieldsets = (
        ("Hazard Zone Information", {
            "fields": ("name", "hazard_type", "risk_level", "description")
        }),
        ("Geographic Data", {
            "fields": ("latitude", "longitude", "coordinates_display")
        }),
    )

    @admin.display(description="Risk Level", ordering="risk_level")
    def get_risk_level_badge(self, obj):
        colors = {
            "LOW": "#17a2b8",
            "MEDIUM": "#ffc107",
            "HIGH": "#ff6c00",
            "CRITICAL": "#dc3545",
        }
        color = colors.get(obj.risk_level, "#6c757d")
        label = dict(HazardZone.RiskLevel.choices).get(obj.risk_level, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            label,
        )

    @admin.display(description="Coordinates")
    def get_coordinates(self, obj):
        return f"{obj.latitude:.4f}, {obj.longitude:.4f}"

    @admin.display(description="Coordinates")
    def coordinates_display(self, obj):
        return f"Latitude: {obj.latitude}, Longitude: {obj.longitude}"

    @admin.display(description="Description")
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:40] + "..." if len(obj.description) > 40 else obj.description
        return "-"


@admin.register(SafeZone)
class SafeZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "get_coordinates", "description_preview")
    search_fields = ("name", "description")
    readonly_fields = ("coordinates_display",)
    ordering = ("name",)

    fieldsets = (
        ("Safe Zone Information", {
            "fields": ("name", "description")
        }),
        ("Geographic Data", {
            "fields": ("latitude", "longitude", "coordinates_display")
        }),
    )

    @admin.display(description="Coordinates")
    def get_coordinates(self, obj):
        return f"{obj.latitude:.4f}, {obj.longitude:.4f}"

    @admin.display(description="Coordinates")
    def coordinates_display(self, obj):
        return f"Latitude: {obj.latitude}, Longitude: {obj.longitude}"

    @admin.display(description="Description")
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:40] + "..." if len(obj.description) > 40 else obj.description
        return "-"

