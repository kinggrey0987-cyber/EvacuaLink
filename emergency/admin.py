from django.contrib import admin
from django.utils.html import format_html

from .models import EmergencyHelpRequest, EmergencyIncident


@admin.register(EmergencyIncident)
class EmergencyIncidentAdmin(admin.ModelAdmin):
    list_display = ("title", "get_severity_badge", "get_status_badge", "location", "reported_at", "reported_by")
    search_fields = ("title", "description", "location")
    list_filter = ("severity", "status", "reported_at")
    readonly_fields = ("reported_at",)
    ordering = ("-reported_at",)

    fieldsets = (
        ("Incident Information", {
            "fields": ("title", "description", "location", "latitude", "longitude")
        }),
        ("Classification", {
            "fields": ("severity", "status")
        }),
        ("Reporting", {
            "fields": ("reported_by", "reported_at", "affected_population")
        }),
        ("Response Details", {
            "fields": ("response_actions", "resolution_notes"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Severity", ordering="severity")
    def get_severity_badge(self, obj):
        colors = {
            "LOW": "#17a2b8",
            "MEDIUM": "#ffc107",
            "HIGH": "#ff6c00",
            "CRITICAL": "#dc3545",
        }
        color = colors.get(obj.severity, "#6c757d")
        label = dict(EmergencyIncident.Severity.choices).get(obj.severity, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            label,
        )

    @admin.display(description="Status", ordering="status")
    def get_status_badge(self, obj):
        colors = {
            "OPEN": "#ffc107",
            "IN_PROGRESS": "#17a2b8",
            "RESOLVED": "#28a745",
            "CLOSED": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        label = dict(EmergencyIncident.Status.choices).get(obj.status, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            label,
        )

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.select_related("reported_by")


@admin.register(EmergencyHelpRequest)
class EmergencyHelpRequestAdmin(admin.ModelAdmin):
    list_display = ("requester_name", "contact_number", "get_status_badge", "location_display", "created_at", "resolution_time")
    search_fields = ("requester_name", "contact_number", "location_description", "message")
    list_filter = ("status", "created_at", "resolved_at")
    readonly_fields = ("created_at", "resolution_time")
    ordering = ("-created_at",)

    fieldsets = (
        ("Requester Information", {
            "fields": ("requester_name", "contact_number")
        }),
        ("Location", {
            "fields": ("location_description", "latitude", "longitude")
        }),
        ("Request Details", {
            "fields": ("message", "priority")
        }),
        ("Status & Resolution", {
            "fields": ("status", "response_notes", "created_at", "resolved_at", "resolution_time"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Status", ordering="status")
    def get_status_badge(self, obj):
        colors = {
            "PENDING": "#ffc107",
            "IN_PROGRESS": "#17a2b8",
            "RESOLVED": "#28a745",
            "CANCELLED": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        label = dict(EmergencyHelpRequest.Status.choices).get(obj.status, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            label,
        )

    @admin.display(description="Location")
    def location_display(self, obj):
        if obj.location_description:
            return obj.location_description[:40] + "..." if len(obj.location_description) > 40 else obj.location_description
        return "-"

    @admin.display(description="Resolution Time")
    def resolution_time(self, obj):
        if obj.resolved_at and obj.created_at:
            delta = obj.resolved_at - obj.created_at
            hours = delta.total_seconds() / 3600
            return f"{int(hours)} hours" if hours >= 1 else f"{int(delta.total_seconds() / 60)} minutes"
        return "-"

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset

