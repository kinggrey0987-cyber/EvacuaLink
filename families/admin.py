from django.contrib import admin
from django.utils.html import format_html

from .models import Family


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("family_code", "family_name", "contact_person", "member_count_display", "reunified_display", "get_reunification_badge")
    search_fields = ("family_code", "family_name", "contact_person", "contact_number")
    list_filter = ("reunification_status", "created_at" if hasattr(Family, "created_at") else "id")
    readonly_fields = ("member_count", "reunited_count", "checked_in_count", "missing_count", "reunification_percentage")
    ordering = ("-id",)

    fieldsets = (
        ("Family Information", {
            "fields": ("family_code", "family_name", "contact_person", "contact_number")
        }),
        ("Reunification Status", {
            "fields": ("reunification_status",)
        }),
        ("Member Statistics", {
            "fields": ("member_count", "reunited_count", "checked_in_count", "missing_count", "reunification_percentage"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Members", ordering="member_count")
    def member_count_display(self, obj):
        return format_html(
            '<strong>{}</strong>',
            obj.member_count,
        )

    @admin.display(description="Reunified", ordering="reunited_count")
    def reunified_display(self, obj):
        percentage = int((obj.reunited_count / obj.member_count) * 100) if obj.member_count > 0 else 0
        return format_html(
            '{}/{} ({}%)',
            obj.reunited_count,
            obj.member_count,
            percentage,
        )

    @admin.display(description="Status", ordering="reunification_status")
    def get_reunification_badge(self, obj):
        colors = {
            "PENDING": "#ffc107",
            "PARTIAL": "#17a2b8",
            "REUNIFIED": "#28a745",
            "UNKNOWN": "#6c757d",
        }
        color = colors.get(obj.reunification_status, "#6c757d")
        label = dict(Family.ReunificationStatus.choices).get(obj.reunification_status, "Unknown")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            label,
        )

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = "Total Members"

    def reunited_count(self, obj):
        return obj.reunited_count
    reunited_count.short_description = "Reunited Members"

    def checked_in_count(self, obj):
        return obj.checked_in_count
    checked_in_count.short_description = "Checked In Members"

    def missing_count(self, obj):
        return obj.missing_count
    missing_count.short_description = "Missing Members"

    def reunification_percentage(self, obj):
        if obj.member_count > 0:
            return f"{int((obj.reunited_count / obj.member_count) * 100)}%"
        return "0%"
    reunification_percentage.short_description = "Reunification Progress"

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("evacuees")

