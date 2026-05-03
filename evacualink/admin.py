"""
Custom Django admin configuration with role-based access control.
Ensures only TECHNICAL_ADMIN users can access the admin site.
"""

from django.contrib import admin
from django.http import HttpResponseForbidden


class EvacuaLinkAdminSite(admin.AdminSite):
    """Custom admin site that restricts access to TECHNICAL_ADMIN users only"""

    site_header = "EvacuaLink Technical Administration"
    site_title = "EvacuaLink Admin"
    index_title = "System Management"

    def has_permission(self, request):
        """
        Override permission check to allow only TECHNICAL_ADMIN users.
        Operational admins should use the operational dashboard instead.
        """
        # First check Django's default permissions
        if not super().has_permission(request):
            return False

        # Additional check: user must be TECHNICAL_ADMIN
        if not request.user.is_technical_admin:
            return False

        return True

    def index(self, request, extra_context=None):
        """Override admin index to provide helpful message to non-technical admins"""
        if not request.user.is_technical_admin:
            return HttpResponseForbidden(
                "<h1>Access Denied</h1>"
                "<p>This area is for technical administrators only.</p>"
                f"<p>Your role: {request.user.get_role_display()}</p>"
                "<p>Operational staff should use the <a href='/users/dashboard/'>operational dashboard</a>.</p>"
            )
        return super().index(request, extra_context)


# Create the custom admin site
evacualink_admin_site = EvacuaLinkAdminSite(name="evacualink_admin")
