from django.contrib import admin
from django.utils.html import format_html

from .models import EvacuationCenter


@admin.register(EvacuationCenter)
class EvacuationCenterAdmin(admin.ModelAdmin):
    list_display = ("name", "get_status_badge", "occupancy_display", "available_space_display", "capacity", "coordinates_display")
    search_fields = ("name", "address", "location")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at", "updated_at", "occupancy_display", "available_space_display")
    ordering = ("name",)

    fieldsets = (
        ("Center Information", {
            "fields": ("name", "location", "address")
        }),
        ("Capacity & Occupancy", {
            "fields": ("capacity", "occupancy_display", "available_space_display")
        }),
        ("Geographic Location", {
            "fields": ("latitude", "longitude")
        }),
        ("Management", {
            "fields": ("status", "manager_contact", "facilities_available")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Status", ordering="status")
    def get_status_badge(self, obj):
        colors = {
            "OPEN": "#28a745",
            "FULL": "#ffc107",
            "CLOSED": "#dc3545",
            "UNDER_MAINTENANCE": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        label = dict(EvacuationCenter.Status.choices).get(obj.status, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            label,
        )

    @admin.display(description="Occupancy")
    def occupancy_display(self, obj):
        occupancy = obj.current_occupancy
        capacity = obj.capacity
        percentage = int((occupancy / capacity) * 100) if capacity > 0 else 0

        # Color code based on occupancy percentage
        if percentage >= 100:
            color = "#dc3545"  # Red for full
        elif percentage >= 80:
            color = "#ffc107"  # Yellow for nearly full
        else:
            color = "#28a745"  # Green for ok

        return format_html(
            '<div style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px; text-align: center;">{}/{} ({}%)</div>',
            color,
            occupancy,
            capacity,
            percentage,
        )

    @admin.display(description="Available Space")
    def available_space_display(self, obj):
        available = obj.available_space()
        if available <= 0:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 4px;">FULL (0 available)</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 4px;">{} available</span>',
            available,
        )

    @admin.display(description="Coordinates")
    def coordinates_display(self, obj):
        return f"{obj.latitude:.4f}, {obj.longitude:.4f}"

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("evacuees")

