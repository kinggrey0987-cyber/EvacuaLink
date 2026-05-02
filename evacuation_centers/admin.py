from django.contrib import admin

from .models import EvacuationCenter


@admin.register(EvacuationCenter)
class EvacuationCenterAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "capacity", "current_occupancy", "display_available_space", "latitude", "longitude")
    search_fields = ("name", "address")
    list_filter = ("status",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Available Space")
    def display_available_space(self, obj):
        return obj.available_space()
