from django.contrib import admin
from django.utils.html import format_html

from .models import Evacuee, TransferRecord


class TransferRecordInline(admin.TabularInline):
    """Inline editing for transfer records"""
    model = TransferRecord
    extra = 0
    readonly_fields = ("transfer_date",)
    fields = ("from_center", "to_center", "transfer_date", "reason")
    ordering = ("-transfer_date",)


@admin.register(Evacuee)
class EvacueeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "age", "gender", "family_link", "evacuation_center", "get_special_needs_badge", "get_status_badge")
    search_fields = ("first_name", "last_name", "family__family_code", "family__family_name")
    list_filter = ("gender", "status", "special_needs", "evacuation_center", "registered_at")
    readonly_fields = ("registered_at", "full_name")
    ordering = ("-registered_at",)
    inlines = [TransferRecordInline]

    fieldsets = (
        ("Personal Information", {
            "fields": ("first_name", "last_name", "full_name", "age", "gender", "id_number")
        }),
        ("Family & Assignment", {
            "fields": ("family", "evacuation_center", "status")
        }),
        ("Special Needs & Medical", {
            "fields": ("special_needs", "special_needs_description", "medical_condition")
        }),
        ("Tracking", {
            "fields": ("registered_at",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Family", ordering="family__family_name")
    def family_link(self, obj):
        if obj.family:
            return format_html(
                '<a href="/admin/families/family/{}/change/">{} ({})</a>',
                obj.family.pk,
                obj.family.family_name,
                obj.family.family_code,
            )
        return "-"

    @admin.display(description="Special Needs", ordering="special_needs")
    def get_special_needs_badge(self, obj):
        if obj.special_needs:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 4px;">Yes</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 4px;">No</span>'
        )

    @admin.display(description="Status", ordering="status")
    def get_status_badge(self, obj):
        colors = {
            "REGISTERED": "#ffc107",
            "CHECKED_IN": "#28a745",
            "TRANSFERRED": "#17a2b8",
            "CHECKED_OUT": "#6c757d",
            "MISSING": "#dc3545",
            "REUNITED": "#0d6efd",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    def get_queryset(self, request):
        """Optimize queryset with selected_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related("family", "evacuation_center")


@admin.register(TransferRecord)
class TransferRecordAdmin(admin.ModelAdmin):
    list_display = ("evacuee", "from_center", "to_center", "transfer_date", "reason_display")
    search_fields = ("evacuee__first_name", "evacuee__last_name", "reason")
    list_filter = ("transfer_date", "from_center", "to_center")
    readonly_fields = ("transfer_date",)
    ordering = ("-transfer_date",)

    fieldsets = (
        ("Transfer Information", {
            "fields": ("evacuee", "from_center", "to_center", "transfer_date")
        }),
        ("Details", {
            "fields": ("reason",)
        }),
    )

    @admin.display(description="Reason")
    def reason_display(self, obj):
        if obj.reason:
            return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
        return "-"

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.select_related("evacuee", "from_center", "to_center")

