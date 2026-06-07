from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import EvacuationCenterForm
from .models import EvacuationCenter


class EvacuationCenterListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = EvacuationCenter
    template_name = "evacuation_centers/center_list.html"
    context_object_name = "centers"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin


class EvacuationCenterDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = EvacuationCenter
    template_name = "evacuation_centers/center_detail.html"
    context_object_name = "center"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from emergency.views import get_safety_map_payload

        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["safety_map_payload"] = get_safety_map_payload()
        return context


class EvacuationCenterCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = EvacuationCenter
    form_class = EvacuationCenterForm
    template_name = "evacuation_centers/center_form.html"
    success_url = reverse_lazy("evacuation-center-list")

    def test_func(self):
        return self.request.user.is_emergency_responder

    def form_valid(self, form):
        messages.success(self.request, "Evacuation center added successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from emergency.views import get_safety_map_payload
        from mapping.utils import get_barangay_center_and_bounds, get_zoom_level_for_bounds

        location_data = get_barangay_center_and_bounds()
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        
        try:
            from mapping.models import SystemSettings
            sys_settings = SystemSettings.get_settings()
            context["is_geofencing_enabled"] = sys_settings.is_geofencing_enabled
        except Exception:
            context["is_geofencing_enabled"] = True
            
        context["safety_map_payload"] = get_safety_map_payload()
        return context


class EvacuationCenterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EvacuationCenter
    form_class = EvacuationCenterForm
    template_name = "evacuation_centers/center_form.html"
    success_url = reverse_lazy("evacuation-center-list")

    def test_func(self):
        return self.request.user.is_emergency_responder

    def form_valid(self, form):
        messages.success(self.request, "Evacuation center updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from emergency.views import get_safety_map_payload
        from mapping.utils import get_barangay_center_and_bounds, get_zoom_level_for_bounds

        location_data = get_barangay_center_and_bounds()
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        
        try:
            from mapping.models import SystemSettings
            sys_settings = SystemSettings.get_settings()
            context["is_geofencing_enabled"] = sys_settings.is_geofencing_enabled
        except Exception:
            context["is_geofencing_enabled"] = True
            
        context["safety_map_payload"] = get_safety_map_payload()
        return context


class EvacuationCenterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = EvacuationCenter
    template_name = "evacuation_centers/center_confirm_delete.html"
    success_url = reverse_lazy("evacuation-center-list")

    def test_func(self):
        return self.request.user.is_emergency_responder

    def form_valid(self, form):
        messages.success(self.request, "Evacuation center deleted successfully.")
        return super().form_valid(form)
