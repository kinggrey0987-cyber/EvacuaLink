from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "report_type", "evacuation_center", "prepared_by", "created_at")
    search_fields = ("title", "content")
    list_filter = ("report_type", "created_at")
