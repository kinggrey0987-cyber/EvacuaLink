from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("EvacuaLink Profile", {"fields": ("role", "phone_number", "address", "is_verified_responder")}),
    )
    list_display = ("username", "get_full_name_display", "email", "get_role_badge", "get_status_badge", "is_staff", "last_login")
    list_filter = ("role", "is_staff", "is_active", "is_verified_responder", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name", "phone_number")
    readonly_fields = ("date_joined", "last_login")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "phone_number", "address")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("EvacuaLink Profile", {"fields": ("role", "is_verified_responder")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    @admin.display(description="Full Name")
    def get_full_name_display(self, obj):
        return obj.get_full_name() or obj.username

    @admin.display(description="Role", ordering="role")
    def get_role_badge(self, obj):
        colors = {
            "TECHNICAL_ADMIN": "#343a40",
            "ADMIN": "#dc3545",
            "STAFF": "#6c757d",
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px;">{}</span>',
            color,
            obj.get_role_display(),
        )

    @admin.display(description="Status", ordering="is_active")
    def get_status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 4px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 4px;">Inactive</span>'
        )

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.select_related()

