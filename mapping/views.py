"""
Views for mapping app - manages evacuation centers, hazard zones, and safe zones.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView

from mapping.models import MapLocation, HazardZone, SafeZone, BarangayBoundary, SystemSettings
from mapping.forms import MapLocationForm, HazardZoneForm, SafeZoneForm, SystemSettingsForm
from mapping.utils import get_barangay_boundary_geojson, get_barangay_center_and_bounds, get_zoom_level_for_bounds


class SystemSettingsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update global system settings (Technical Admin only)"""
    
    model = SystemSettings
    form_class = SystemSettingsForm
    template_name = "mapping/system_settings.html"
    success_url = reverse_lazy("system-settings")

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_technical_admin

    def get_object(self, queryset=None):
        return SystemSettings.get_settings()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        return context
class PublicMapView(TemplateView):
    """Public-facing map showing evacuation centers, hazard zones, and safe zones"""

    template_name = "mapping/public_map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all active locations
        evacuation_centers = list(
            MapLocation.objects.filter(
                location_type="EVACUATION_CENTER", is_active=True
            ).values("id", "name", "latitude", "longitude",  "description")
        )

        hazard_zones = list(
            HazardZone.objects.all().values(
                "id", "name", "latitude", "longitude", "hazard_type", "risk_level", "description"
            )
        )

        safe_zones = list(
            SafeZone.objects.all().values(
                "id", "name", "latitude", "longitude", "description"
            )
        )

        # Get boundary and center info
        boundary_geojson = get_barangay_boundary_geojson()
        location_data = get_barangay_center_and_bounds()

        context["evacuation_centers"] = evacuation_centers
        context["hazard_zones"] = hazard_zones
        context["safe_zones"] = safe_zones
        context["boundary_geojson"] = boundary_geojson
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["public_map_payload"] = {
            "center": location_data["center"],
            "bounds": location_data["bounds"],
            "boundary": boundary_geojson,
            "evacuationCenters": evacuation_centers,
            "hazardZones": hazard_zones,
            "safeZones": safe_zones,
        }

        return context


class AdminMapView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin map for managing locations with add/edit capabilities"""

    template_name = "mapping/admin_map.html"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all active locations
        evacuation_centers = list(
            MapLocation.objects.filter(
                location_type="EVACUATION_CENTER", is_active=True
            ).values("id", "name", "latitude", "longitude", "description")
        )

        hazard_zones = list(
            HazardZone.objects.all().values(
                "id", "name", "latitude", "longitude", "hazard_type", "risk_level", "description"
            )
        )

        safe_zones = list(
            SafeZone.objects.all().values(
                "id", "name", "latitude", "longitude", "description"
            )
        )

        # Get boundary and center info
        boundary_geojson = get_barangay_boundary_geojson()
        location_data = get_barangay_center_and_bounds()

        context["evacuation_centers"] = evacuation_centers
        context["hazard_zones"] = hazard_zones
        context["safe_zones"] = safe_zones
        context["boundary_geojson"] = boundary_geojson
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["admin_map_payload"] = {
            "center": location_data["center"],
            "bounds": location_data["bounds"],
            "boundary": boundary_geojson,
            "evacuationCenters": evacuation_centers,
            "hazardZones": hazard_zones,
            "safeZones": safe_zones,
        }

        return context


class MapLocationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all map locations"""

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    model = MapLocation
    template_name = "mapping/maplocation_list.html"
    context_object_name = "locations"
    paginate_by = 20

    def get_queryset(self):
        return MapLocation.objects.filter(is_active=True).order_by("name")


class MapLocationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new map location"""

    model = MapLocation
    form_class = MapLocationForm
    template_name = "mapping/maplocation_form.html"
    success_url = reverse_lazy("map-location-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class MapLocationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing map location"""

    model = MapLocation
    form_class = MapLocationForm
    template_name = "mapping/maplocation_form.html"
    success_url = reverse_lazy("map-location-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class HazardZoneListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all hazard zones"""

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    model = HazardZone
    template_name = "mapping/hazardzone_list.html"
    context_object_name = "hazard_zones"
    paginate_by = 20

    def get_queryset(self):
        return HazardZone.objects.all().order_by("name")


class HazardZoneCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new hazard zone"""

    model = HazardZone
    form_class = HazardZoneForm
    template_name = "mapping/hazardzone_form.html"
    success_url = reverse_lazy("hazard-zone-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class HazardZoneUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing hazard zone"""

    model = HazardZone
    form_class = HazardZoneForm
    template_name = "mapping/hazardzone_form.html"
    success_url = reverse_lazy("hazard-zone-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class HazardZoneDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a hazard zone"""

    model = HazardZone
    template_name = "mapping/hazardzone_confirm_delete.html"
    success_url = reverse_lazy("hazard-zone-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class SafeZoneListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all safe zones"""

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    model = SafeZone
    template_name = "mapping/safezone_list.html"
    context_object_name = "safe_zones"
    paginate_by = 20

    def get_queryset(self):
        return SafeZone.objects.all().order_by("name")


class SafeZoneCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new safe zone"""

    model = SafeZone
    form_class = SafeZoneForm
    template_name = "mapping/safezone_form.html"
    success_url = reverse_lazy("safe-zone-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class SafeZoneUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing safe zone"""

    model = SafeZone
    form_class = SafeZoneForm
    template_name = "mapping/safezone_form.html"
    success_url = reverse_lazy("safe-zone-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class SafeZoneDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a safe zone"""

    model = SafeZone
    template_name = "mapping/safezone_confirm_delete.html"
    success_url = reverse_lazy("safe-zone-list")

    def test_func(self):
        return self.request.user.is_emergency_responder


class MapAPIView(View):
    """API endpoint returning map data as JSON"""

    def get(self, request):
        """Return all map locations as JSON"""
        locations = [
            {
                "id": location.id,
                "name": location.name,
                "location_type": location.location_type,
                "coordinates": location.coordinates,
                "description": location.description,
            }
            for location in MapLocation.objects.filter(is_active=True)
        ]
        return JsonResponse({"map_locations": locations})
