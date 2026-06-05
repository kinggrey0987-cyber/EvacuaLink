from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import EvacuationCenterForm
from .models import EvacuationCenter


class EvacuationCenterListView(LoginRequiredMixin, ListView):
    model = EvacuationCenter
    template_name = "evacuation_centers/center_list.html"
    context_object_name = "centers"


class EvacuationCenterDetailView(LoginRequiredMixin, DetailView):
    model = EvacuationCenter
    template_name = "evacuation_centers/center_detail.html"
    context_object_name = "center"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
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


class EvacuationCenterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = EvacuationCenter
    template_name = "evacuation_centers/center_confirm_delete.html"
    success_url = reverse_lazy("evacuation-center-list")

    def test_func(self):
        return self.request.user.is_operational_admin

    def form_valid(self, form):
        messages.success(self.request, "Evacuation center deleted successfully.")
        return super().form_valid(form)
