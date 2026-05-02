from django.contrib import admin

from .models import EmergencyHelpRequest, EmergencyIncident


@admin.register(EmergencyIncident)
class EmergencyIncidentAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "status", "location", "reported_at")
    search_fields = ("title", "description", "location")
    list_filter = ("severity", "status", "reported_at")


@admin.register(EmergencyHelpRequest)
class EmergencyHelpRequestAdmin(admin.ModelAdmin):
    list_display = ("requester_name", "contact_number", "status", "created_at", "resolved_at")
    search_fields = ("requester_name", "contact_number", "location_description", "message")
    list_filter = ("status", "created_at", "resolved_at")
    readonly_fields = ("created_at",)
