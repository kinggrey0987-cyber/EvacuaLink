from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
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


class EvacuationCenterCreateView(LoginRequiredMixin, CreateView):
    model = EvacuationCenter
    form_class = EvacuationCenterForm
    template_name = "evacuation_centers/center_form.html"
    success_url = reverse_lazy("evacuation-center-list")

    def form_valid(self, form):
        messages.success(self.request, "Evacuation center added successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class EvacuationCenterUpdateView(LoginRequiredMixin, UpdateView):
    model = EvacuationCenter
    form_class = EvacuationCenterForm
    template_name = "evacuation_centers/center_form.html"
    success_url = reverse_lazy("evacuation-center-list")

    def form_valid(self, form):
        messages.success(self.request, "Evacuation center updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class EvacuationCenterDeleteView(LoginRequiredMixin, DeleteView):
    model = EvacuationCenter
    template_name = "evacuation_centers/center_confirm_delete.html"
    success_url = reverse_lazy("evacuation-center-list")

    def form_valid(self, form):
        messages.success(self.request, "Evacuation center deleted successfully.")
        return super().form_valid(form)
