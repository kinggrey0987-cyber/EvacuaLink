from django.urls import path

from .views import (
    FamilyDashboardView,
    FamilyDeleteView,
    FamilyDetailView,
    FamilyListView,
    FamilyRegistrationView,
    FamilyReunificationUpdateView,
    FamilyUpdateView,
)

urlpatterns = [
    path("dashboard/", FamilyDashboardView.as_view(), name="family-dashboard"),
    path("", FamilyListView.as_view(), name="family-list"),
    path("register/", FamilyRegistrationView.as_view(), name="family-register"),
    path("<int:pk>/", FamilyDetailView.as_view(), name="family-detail"),
    path("<int:pk>/edit/", FamilyUpdateView.as_view(), name="family-edit"),
    path("<int:pk>/reunification/", FamilyReunificationUpdateView.as_view(), name="family-reunification"),
    path("<int:pk>/delete/", FamilyDeleteView.as_view(), name="family-delete"),
]
