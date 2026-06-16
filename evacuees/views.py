"""
Views for evacuee management system.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    FormView,
    TemplateView,
)

from evacuees.forms import (
    EvacueeRegistrationForm,
    EvacueeAssignmentForm,
    EvacueeStatusForm,
    EvacueeUpdateForm,
    EvacueeTransferForm,
)
from evacuees.models import Evacuee, TransferRecord
from evacuees.services import recalculate_centers_occupancy
from families.models import Family


class EvacueeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all evacuees with filtering options"""

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    model = Evacuee
    template_name = "evacuees/evacuee_list.html"
    context_object_name = "evacuees"
    paginate_by = 5

    def get_queryset(self):
        queryset = Evacuee.objects.select_related("family", "evacuation_center").order_by("-id")

        # Filter by center if provided
        center_id = self.request.GET.get("evacuation_center")
        if center_id:
            queryset = queryset.filter(evacuation_center_id=center_id)

        # Filter by special needs if provided
        special_needs = self.request.GET.get("special_needs")
        if special_needs in {"true", "false"}:
            queryset = queryset.filter(special_needs=(special_needs == "true"))

        # Filter by status if provided
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by family if provided
        family_id = self.request.GET.get("family")
        if family_id:
            queryset = queryset.filter(family_id=family_id)

        return queryset.order_by("family", "last_name", "first_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from evacuation_centers.models import EvacuationCenter

        context["centers"] = EvacuationCenter.objects.all()
        context["families"] = Family.objects.all()
        context["statuses"] = Evacuee.Status.choices
        context["selected_center"] = self.request.GET.get("evacuation_center", "")
        context["selected_special_needs"] = self.request.GET.get("special_needs", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_family"] = self.request.GET.get("family", "")

        # Statistics
        context["total_evacuees"] = Evacuee.objects.count()
        context["checked_in"] = Evacuee.objects.filter(status="CHECKED_IN").count()
        context["special_needs_count"] = Evacuee.objects.filter(special_needs=True).count()

        return context


class EvacueeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View detailed information about an evacuee"""

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    model = Evacuee
    template_name = "evacuees/evacuee_detail.html"
    context_object_name = "evacuee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evacuee = self.get_object()
        from emergency.views import get_safety_map_payload

        # Get transfer history
        context["transfers"] = evacuee.transfer_records.all()
        # Get family members
        context["family_members"] = evacuee.family.evacuees.exclude(id=evacuee.id)
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["safety_map_payload"] = get_safety_map_payload()

        return context


class EvacueeRegistrationView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Register a new evacuee"""

    model = Evacuee
    form_class = EvacueeRegistrationForm
    template_name = "evacuees/evacuee_register.html"
    success_url = reverse_lazy("evacuee-list")
    success_message = "Evacuee '%(first_name)s %(last_name)s' registered successfully!"

    def test_func(self):
        return self.request.user.is_emergency_responder

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Register New Evacuee"
        return context


class EvacueeAssignmentView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, FormView):
    """Assign an evacuee to an evacuation center"""

    form_class = EvacueeAssignmentForm
    template_name = "evacuees/evacuee_assign.html"
    success_url = reverse_lazy("evacuee-list")

    def test_func(self):
        return self.request.user.is_emergency_responder

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from emergency.views import get_safety_map_payload
        from mapping.utils import get_barangay_center_and_bounds, get_zoom_level_for_bounds

        evacuee_id = self.kwargs.get("pk")
        context["evacuee"] = get_object_or_404(Evacuee, pk=evacuee_id)

        location_data = get_barangay_center_and_bounds()
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["safety_map_payload"] = get_safety_map_payload()
        return context

    def form_valid(self, form):
        evacuee_id = self.kwargs.get("pk")
        evacuee = get_object_or_404(Evacuee, pk=evacuee_id)

        # Assign to center and change status to CHECKED_IN
        center = form.cleaned_data["evacuation_center"]
        if center.is_full():
            form.add_error("evacuation_center", "This evacuation center is already full.")
            return self.form_invalid(form)

        with transaction.atomic():
            evacuee.evacuation_center = center
            evacuee.status = "CHECKED_IN"
            evacuee.save()
            recalculate_centers_occupancy(center)

        messages.success(
            self.request,
            f"{evacuee.full_name} assigned to {center.name}",
        )
        return super().form_valid(form)


class EvacueeStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update evacuee status"""

    model = Evacuee
    form_class = EvacueeStatusForm
    template_name = "evacuees/evacuee_status.html"
    success_url = reverse_lazy("evacuee-list")
    success_message = "Status updated for %(first_name)s %(last_name)s"

    def test_func(self):
        return self.request.user.is_emergency_responder

    def form_valid(self, form):
        old_evacuee = Evacuee.objects.select_related("evacuation_center").get(pk=self.object.pk)
        response = super().form_valid(form)
        self.object.refresh_from_db()
        recalculate_centers_occupancy(old_evacuee.evacuation_center, self.object.evacuation_center)
        return response


class EvacueeUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update evacuee information"""

    model = Evacuee
    form_class = EvacueeUpdateForm
    template_name = "evacuees/evacuee_form.html"
    success_url = reverse_lazy("evacuee-list")
    success_message = "Evacuee information updated for %(first_name)s %(last_name)s"

    def test_func(self):
        return self.request.user.is_emergency_responder


class EvacueeTransferView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Transfer evacuee to another center"""

    model = TransferRecord
    form_class = EvacueeTransferForm
    template_name = "evacuees/evacuee_transfer.html"
    success_url = reverse_lazy("evacuee-list")
    success_message = "Transfer recorded for evacuee"

    def test_func(self):
        return self.request.user.is_emergency_responder

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        evacuee_id = self.kwargs.get("pk")
        evacuee = get_object_or_404(Evacuee, pk=evacuee_id)
        kwargs["evacuee"] = evacuee
        return kwargs

    def form_valid(self, form):
        evacuee_id = self.kwargs.get("pk")
        evacuee = get_object_or_404(Evacuee, pk=evacuee_id)
        old_center = evacuee.evacuation_center
        new_center = form.cleaned_data["to_center"]

        if new_center.is_full():
            form.add_error("to_center", "The destination center is already full.")
            return self.form_invalid(form)

        with transaction.atomic():
            # Create transfer record
            transfer = form.save(commit=False)
            transfer.evacuee = evacuee
            transfer.from_center = old_center
            transfer.save()

            # Update evacuee's current center
            evacuee.evacuation_center = new_center
            evacuee.status = "TRANSFERRED"
            evacuee.save()

            recalculate_centers_occupancy(old_center, new_center)

        messages.success(
            self.request,
            f"{evacuee.full_name} transferred to {new_center.name}",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evacuee_id = self.kwargs.get("pk")
        context["evacuee"] = get_object_or_404(Evacuee, pk=evacuee_id)
        return context


class EvacueeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an evacuee record"""

    model = Evacuee
    template_name = "evacuees/evacuee_confirm_delete.html"
    success_url = reverse_lazy("evacuee-list")

    def test_func(self):
        return self.request.user.is_emergency_responder

    def form_valid(self, form):
        evacuee = self.get_object()
        center = evacuee.evacuation_center
        messages.success(request, f"Evacuee '{evacuee.full_name}' deleted successfully.")
        response = super().form_valid(form)
        recalculate_centers_occupancy(center)
        return response


class EvacueeDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Evacuee management dashboard"""

    template_name = "evacuees/evacuee_dashboard.html"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistics
        context["total_evacuees"] = Evacuee.objects.count()
        context["registered"] = Evacuee.objects.filter(status="REGISTERED").count()
        context["checked_in"] = Evacuee.objects.filter(status="CHECKED_IN").count()
        context["checked_out"] = Evacuee.objects.filter(status="CHECKED_OUT").count()
        context["transferred"] = Evacuee.objects.filter(status="TRANSFERRED").count()
        context["reunited"] = Evacuee.objects.filter(status="REUNITED").count()
        context["missing"] = Evacuee.objects.filter(status="MISSING").count()

        # Special needs
        context["special_needs_count"] = Evacuee.objects.filter(special_needs=True).count()

        # Recent evacuees
        context["recent_evacuees"] = Evacuee.objects.select_related("family", "evacuation_center")[
            :10
        ]

        # Recent transfers
        context["recent_transfers"] = TransferRecord.objects.select_related("evacuee")[
            :10
        ]

        return context

