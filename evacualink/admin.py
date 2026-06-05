"""
Custom Django admin configuration with role-based access control.
Ensures only technical administrator users can access the admin site.
"""

from django.contrib import admin
from django.http import HttpResponseForbidden


class EvacuaLinkAdminSite(admin.AdminSite):
    """Custom admin site that restricts access to technical administrator users."""

    site_header = "EvacuaLink Technical Administration"
    site_title = "EvacuaLink Admin"
    index_title = "System Management"

    def has_permission(self, request):
        """
        Override permission check to allow only technical administrator users.
        """
        # First check Django's default permissions
        if not super().has_permission(request):
            return False

        if not request.user.is_technical_admin:
            return False

        return True

    def index(self, request, extra_context=None):
        """Override admin index to provide helpful message to non-technical users."""
        if not request.user.is_technical_admin:
            return HttpResponseForbidden(
                "<h1>Access Denied</h1>"
                "<p>This area is for technical administrators only.</p>"
                f"<p>Your role: {request.user.get_role_display()}</p>"
                "<p>Admin and staff users should use the <a href='/dashboard/'>operational dashboard</a>.</p>"
            )
        return super().index(request, extra_context)


# Create the custom admin site
evacualink_admin_site = EvacuaLinkAdminSite(name="evacualink_admin")
