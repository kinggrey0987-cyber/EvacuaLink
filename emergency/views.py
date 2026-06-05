"""
Views for emergency management system.
Includes public help requests and admin incident tracking.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    TemplateView,
    DetailView,
)
from django.utils import timezone
from django.db.models import Q
import json

from emergency.models import EmergencyHelpRequest, EmergencyHelpRequestStatusLog, EmergencyIncident
from emergency.forms import (
    EmergencyHelpRequestForm,
    EmergencyHelpRequestStatusForm,
    EmergencyIncidentForm,
)


def get_safety_map_payload():
    from evacuation_centers.models import EvacuationCenter
    from mapping.models import BarangayBoundary, HazardZone, SafeZone
    from mapping.utils import get_barangay_boundary_geojson, get_barangay_center_and_bounds

    location_data = get_barangay_center_and_bounds()
    evacuation_centers = list(
        EvacuationCenter.objects.all().values("id", "name", "latitude", "longitude", "address")
    )
    hazard_zones = list(
        HazardZone.objects.all().values(
            "id", "name", "latitude", "longitude", "hazard_type", "risk_level", "description"
        )
    )
    safe_zones = list(
        SafeZone.objects.all().values("id", "name", "latitude", "longitude", "description")
    )
    boundary = BarangayBoundary.objects.first()

    def inside_boundary(item):
        if not boundary:
            return True
        return boundary.contains_point(float(item["latitude"]), float(item["longitude"]))

    evacuation_centers = [center for center in evacuation_centers if inside_boundary(center)]
    hazard_zones = [zone for zone in hazard_zones if inside_boundary(zone)]
    safe_zones = [zone for zone in safe_zones if inside_boundary(zone)]

    return {
        "center": location_data["center"],
        "bounds": location_data["bounds"],
        "boundary": get_barangay_boundary_geojson(),
        "evacuationCenters": evacuation_centers,
        "hazardZones": hazard_zones,
        "safeZones": safe_zones,
    }


class PublicHelpRequestView(CreateView):
    """Public form for submitting emergency help requests"""

    model = EmergencyHelpRequest
    form_class = EmergencyHelpRequestForm
    template_name = "emergency/help_request_form.html"
    success_url = reverse_lazy("help-request-success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from mapping.utils import get_barangay_center_and_bounds, get_zoom_level_for_bounds

        location_data = get_barangay_center_and_bounds()
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["safety_map_payload"] = get_safety_map_payload()
        return context


class HelpRequestSuccessView(TemplateView):
    """Success page after submitting help request"""

    template_name = "emergency/help_request_success.html"


class HelpRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all help requests (emergency responders only)"""

    model = EmergencyHelpRequest
    template_name = "emergency/helprequest_list.html"
    context_object_name = "help_requests"
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_queryset(self):
        queryset = EmergencyHelpRequest.objects.select_related("assigned_to").order_by("-created_at")

        # Filter by status if provided
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = EmergencyHelpRequest.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["pending_count"] = EmergencyHelpRequest.objects.filter(status="PENDING").count()
        context["in_progress_count"] = EmergencyHelpRequest.objects.filter(status="IN_PROGRESS").count()
        return context


class HelpRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View details of a specific help request"""

    model = EmergencyHelpRequest
    template_name = "emergency/helprequest_detail.html"
    context_object_name = "request"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from mapping.utils import get_barangay_center_and_bounds, get_zoom_level_for_bounds

        location_data = get_barangay_center_and_bounds()
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["safety_map_payload"] = get_safety_map_payload()
        return context


class HelpRequestUpdateStatusView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update help request status (admin/responders only)"""

    model = EmergencyHelpRequest
    form_class = EmergencyHelpRequestStatusForm
    template_name = "emergency/helprequest_update_status.html"
    success_url = reverse_lazy("help-request-list")
    success_message = "Help request status updated successfully"

    def test_func(self):
        return self.request.user.is_emergency_responder

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["help_request"] = self.get_object()
        return context

    def form_valid(self, form):
        old_request = EmergencyHelpRequest.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        notes = form.cleaned_data.get("response_notes", "")
        if (
            old_request.status != self.object.status
            or old_request.priority != self.object.priority
            or old_request.assigned_to_id != self.object.assigned_to_id
            or notes
        ):
            EmergencyHelpRequestStatusLog.objects.create(
                help_request=self.object,
                old_status=old_request.status,
                new_status=self.object.status,
                priority=self.object.priority,
                assigned_to=self.object.assigned_to,
                notes=notes,
                updated_by=self.request.user,
            )
        return response


class EmergencyIncidentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all emergency incidents (responders only)"""

    model = EmergencyIncident
    template_name = "emergency/incident_list.html"
    context_object_name = "incidents"
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_queryset(self):
        queryset = EmergencyIncident.objects.all().order_by("-reported_at")

        # Filter by status
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by severity
        severity_filter = self.request.GET.get("severity")
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = EmergencyIncident.Status.choices
        context["severities"] = EmergencyIncident.Severity.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_severity"] = self.request.GET.get("severity", "")
        context["critical_count"] = EmergencyIncident.objects.filter(severity="CRITICAL").count()
        context["open_count"] = EmergencyIncident.objects.filter(status="OPEN").count()
        return context


class EmergencyIncidentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View details of a specific incident"""

    model = EmergencyIncident
    template_name = "emergency/incident_detail.html"
    context_object_name = "incident"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin


class EmergencyIncidentCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Create a new emergency incident"""

    model = EmergencyIncident
    form_class = EmergencyIncidentForm
    template_name = "emergency/incident_form.html"
    success_url = reverse_lazy("emergency-incident-list")
    success_message = "Emergency incident created successfully"

    def test_func(self):
        return self.request.user.is_emergency_responder

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        return super().form_valid(form)


class EmergencyIncidentUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update an existing emergency incident"""

    model = EmergencyIncident
    form_class = EmergencyIncidentForm
    template_name = "emergency/incident_form.html"
    success_url = reverse_lazy("emergency-incident-list")
    success_message = "Emergency incident updated successfully"

    def test_func(self):
        return self.request.user.is_emergency_responder


class EmergencyDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard for emergency management overview"""

    template_name = "emergency/emergency_dashboard.html"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Help request statistics
        help_requests = EmergencyHelpRequest.objects.all()
        context["total_help_requests"] = help_requests.count()
        context["pending_requests"] = help_requests.filter(status="PENDING").count()
        context["in_progress_requests"] = help_requests.filter(status="IN_PROGRESS").count()
        context["recent_requests"] = help_requests[:5]
        context["active_help_request_markers"] = json.dumps(
            list(
                help_requests.exclude(status__in=["RESOLVED", "CANCELLED"]).values(
                    "id",
                    "requester_name",
                    "contact_number",
                    "location_description",
                    "latitude",
                    "longitude",
                    "location_source",
                    "location_accuracy",
                    "status",
                    "created_at",
                )
            ),
            cls=DjangoJSONEncoder,
        )

        # Emergency incident statistics
        incidents = EmergencyIncident.objects.all()
        context["total_incidents"] = incidents.count()
        context["open_incidents"] = incidents.filter(status="OPEN").count()
        context["critical_incidents"] = incidents.filter(severity="CRITICAL").count()
        context["recent_incidents"] = incidents[:5]

        # High severity/priority alerts
        context["alerts"] = incidents.filter(
            Q(status="OPEN") & Q(severity__in=["CRITICAL", "HIGH"])
        ).order_by("-reported_at")[:10]
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["safety_map_payload"] = get_safety_map_payload()

        return context


class EmergencyIncidentJSONListView(View):
    """API endpoint returning emergency incidents as JSON"""

    def get(self, request):
        """Return incidents as JSON for map display"""
        incidents = list(
            EmergencyIncident.objects.values(
                "id",
                "title",
                "location",
                "severity",
                "status",
                "reported_at",
            )
        )
        return JsonResponse({"incidents": incidents})


class HelpRequestJSONListView(LoginRequiredMixin, UserPassesTestMixin, View):
    """API endpoint returning help requests as JSON"""

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get(self, request):
        """Return help requests as JSON for map display"""
        help_requests = list(
            EmergencyHelpRequest.objects.values(
                "id",
                "requester_name",
                "contact_number",
                "location_description",
                "latitude",
                "longitude",
                "location_source",
                "location_accuracy",
                "status",
                "created_at",
            )
        )
        return JsonResponse({"help_requests": help_requests})
