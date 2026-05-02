from django.urls import path

from .views import (
    PublicHelpRequestView,
    HelpRequestSuccessView,
    HelpRequestListView,
    HelpRequestDetailView,
    HelpRequestUpdateStatusView,
    EmergencyIncidentListView,
    EmergencyIncidentDetailView,
    EmergencyIncidentCreateView,
    EmergencyIncidentUpdateView,
    EmergencyDashboardView,
    EmergencyIncidentJSONListView,
    HelpRequestJSONListView,
)

urlpatterns = [
    # Emergency Dashboard
    path("dashboard/", EmergencyDashboardView.as_view(), name="emergency-dashboard"),

    # Public Help Request
    path("help-request/", PublicHelpRequestView.as_view(), name="help-request"),
    path("help-request/success/", HelpRequestSuccessView.as_view(), name="help-request-success"),

    # Help Requests (Admin)
    path("help-requests/", HelpRequestListView.as_view(), name="help-request-list"),
    path("help-requests/<int:pk>/", HelpRequestDetailView.as_view(), name="help-request-detail"),
    path("help-requests/<int:pk>/update-status/", HelpRequestUpdateStatusView.as_view(), name="help-request-update-status"),

    # Emergency Incidents
    path("incidents/", EmergencyIncidentListView.as_view(), name="emergency-incident-list"),
    path("incidents/create/", EmergencyIncidentCreateView.as_view(), name="emergency-incident-create"),
    path("incidents/<int:pk>/", EmergencyIncidentDetailView.as_view(), name="emergency-incident-detail"),
    path("incidents/<int:pk>/edit/", EmergencyIncidentUpdateView.as_view(), name="emergency-incident-edit"),

    # API Endpoints
    path("api/incidents/", EmergencyIncidentJSONListView.as_view(), name="emergency-api-incidents"),
    path("api/help-requests/", HelpRequestJSONListView.as_view(), name="emergency-api-help-requests"),
]

