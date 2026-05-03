from django.contrib import admin
from django.utils.html import format_html

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "get_report_type_badge", "evacuation_center", "prepared_by", "created_at")
    search_fields = ("title", "content")
    list_filter = ("report_type", "created_at", "evacuation_center")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Report Information", {
            "fields": ("title", "report_type", "description")
        }),
        ("Content", {
            "fields": ("content",)
        }),
        ("Context", {
            "fields": ("evacuation_center", "prepared_by")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Report Type", ordering="report_type")
    def get_report_type_badge(self, obj):
        colors = {
            "OCCUPANCY": "#17a2b8",
            "INCIDENT": "#dc3545",
            "SUPPLIES": "#ffc107",
            "EVACUEE_SUMMARY": "#28a745",
        }
        color = colors.get(obj.report_type, "#6c757d")
        label = dict(Report.ReportType.choices).get(obj.report_type, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            label,
        )

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.select_related("evacuation_center", "prepared_by")

