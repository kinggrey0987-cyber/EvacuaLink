from django.contrib import admin
from django.utils.html import format_html

from .models import EmergencyHelpRequest, EmergencyHelpRequestStatusLog, EmergencyIncident


@admin.register(EmergencyIncident)
class EmergencyIncidentAdmin(admin.ModelAdmin):
    list_display = ("title", "get_severity_badge", "get_status_badge", "location", "reported_at", "reported_by")
    search_fields = ("title", "description", "location")
    list_filter = ("severity", "status", "reported_at")
    readonly_fields = ("reported_at",)
    ordering = ("-reported_at",)

    fieldsets = (
        ("Incident Information", {
            "fields": ("title", "description", "location", "evacuation_center")
        }),
        ("Classification", {
            "fields": ("severity", "status")
        }),
        ("Reporting", {
            "fields": ("reported_by", "reported_at", "resolved_at")
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
    list_display = ("requester_name", "contact_number", "get_priority_badge", "get_status_badge", "assigned_to", "location_display", "location_source", "has_photo", "created_at", "resolution_time")
    search_fields = ("requester_name", "contact_number", "location_description", "message", "response_notes")
    list_filter = ("priority", "status", "assigned_to", "location_source", "created_at", "resolved_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Requester Information", {
            "fields": ("requester_name", "contact_number")
        }),
        ("Location", {
            "fields": ("location_description", "latitude", "longitude", "location_source", "location_accuracy")
        }),
        ("Request Details", {
            "fields": ("message", "photo", "photo_preview")
        }),
        ("Status & Resolution", {
            "fields": ("priority", "status", "assigned_to", "response_notes", "created_at", "resolved_at", "resolution_time"),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("created_at", "resolution_time", "photo_preview")

    @admin.display(description="Priority", ordering="priority")
    def get_priority_badge(self, obj):
        colors = {
            "LOW": "#6c757d",
            "NORMAL": "#0d6efd",
            "HIGH": "#ff6c00",
            "CRITICAL": "#dc3545",
        }
        color = colors.get(obj.priority, "#6c757d")
        label = dict(EmergencyHelpRequest.Priority.choices).get(obj.priority, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            label,
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

    @admin.display(description="Photo", boolean=True)
    def has_photo(self, obj):
        return bool(obj.photo)

    @admin.display(description="Photo Preview")
    def photo_preview(self, obj):
        if not obj.photo:
            return "-"

        return format_html(
            '<a href="{}" target="_blank"><img src="{}" style="max-width: 260px; max-height: 180px; border-radius: 6px;" alt="Help request photo"></a>',
            obj.photo.url,
            obj.photo.url,
        )

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
        return queryset.select_related("assigned_to")


@admin.register(EmergencyHelpRequestStatusLog)
class EmergencyHelpRequestStatusLogAdmin(admin.ModelAdmin):
    list_display = ("help_request", "old_status", "new_status", "priority", "assigned_to", "updated_by", "created_at")
    list_filter = ("new_status", "priority", "created_at")
    search_fields = ("help_request__requester_name", "notes")
    readonly_fields = ("created_at",)
