"""Root URL configuration for EvacuaLink."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from users.views import LoginView, LogoutView

urlpatterns = [
    path("", RedirectView.as_view(url="users/dashboard/", permanent=False), name="home"),
    path("admin/", admin.site.urls),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("users/", include("users.urls")),
    path("families/", include("families.urls")),
    path("evacuation-centers/", include("evacuation_centers.urls")),
    path("evacuees/", include("evacuees.urls")),
    path("emergency/", include("emergency.urls")),
    path("reports/", include("reports.urls")),
    path("mapping/", include("mapping.urls")),
]
