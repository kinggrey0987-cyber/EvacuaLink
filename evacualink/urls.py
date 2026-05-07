"""Root URL configuration for EvacuaLink."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from users.views import LoginView, LogoutView, OperationalDashboardView, PublicLandingPageView
from .admin import evacualink_admin_site

urlpatterns = [
    # Public Landing Page (no login required)
    path("", PublicLandingPageView.as_view(), name="home"),

    # Operational Dashboard (for ADMIN, COORDINATOR, VOLUNTEER, STAFF)
    path("dashboard/", OperationalDashboardView.as_view(), name="dashboard"),

    # Django Admin (TECHNICAL_ADMIN only)
    path("admin/", evacualink_admin_site.urls),

    # Authentication
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # App URLs
    path("users/", include("users.urls")),
    path("families/", include("families.urls")),
    path("evacuation-centers/", include("evacuation_centers.urls")),
    path("evacuees/", include("evacuees.urls")),
    path("emergency/", include("emergency.urls")),
    path("reports/", include("reports.urls")),
    path("mapping/", include("mapping.urls")),
]

