from django.urls import path

from .views import (
    EvacueeListView,
    EvacueeDetailView,
    EvacueeRegistrationView,
    EvacueeAssignmentView,
    EvacueeStatusUpdateView,
    EvacueeUpdateView,
    EvacueeTransferView,
    EvacueeDeleteView,
    EvacueeDashboardView,
)

urlpatterns = [
    # Dashboard
    path("dashboard/", EvacueeDashboardView.as_view(), name="evacuee-dashboard"),

    # List and Registration
    path("", EvacueeListView.as_view(), name="evacuee-list"),
    path("register/", EvacueeRegistrationView.as_view(), name="evacuee-register"),

    # Details and Updates
    path("<int:pk>/", EvacueeDetailView.as_view(), name="evacuee-detail"),
    path("<int:pk>/edit/", EvacueeUpdateView.as_view(), name="evacuee-edit"),
    path("<int:pk>/assign/", EvacueeAssignmentView.as_view(), name="evacuee-assign"),
    path("<int:pk>/status/", EvacueeStatusUpdateView.as_view(), name="evacuee-status"),
    path("<int:pk>/transfer/", EvacueeTransferView.as_view(), name="evacuee-transfer"),
    path("<int:pk>/delete/", EvacueeDeleteView.as_view(), name="evacuee-delete"),
]

