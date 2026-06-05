"""
Views for family management and reunification tracking.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    TemplateView,
)

from families.forms import (
    FamilyRegistrationForm,
    FamilyUpdateForm,
    FamilyReunificationForm,
)
from families.models import Family
from families.models import FamilyReunificationLog


class FamilyDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Family management dashboard with statistics"""

    template_name = "families/family_dashboard.html"

    def test_func(self):
        return self.request.user.is_emergency_responder or self.request.user.is_operational_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_families = Family.objects.all()

        # Statistics
        context["total_families"] = all_families.count()
        context["pending_families"] = all_families.filter(reunification_status="PENDING").count()
        context["partial_families"] = all_families.filter(reunification_status="PARTIAL").count()
        context["reunified_families"] = all_families.filter(reunification_status="REUNIFIED").count()

        # Recent families
        context["recent_families"] = all_families.prefetch_related("evacuees")[:10]

        # Families needing attention (with missing members)
        families_with_missing = []
        for family in all_families:
            if family.missing_count > 0:
                families_with_missing.append(family)
        context["families_with_missing"] = families_with_missing[:5]

        return context


class FamilyListView(LoginRequiredMixin, ListView):
    """List all families with filtering and statistics"""

    model = Family
    template_name = "families/family_list.html"
    context_object_name = "families"
    paginate_by = 20

    def get_queryset(self):
        queryset = Family.objects.prefetch_related("evacuees")

        # Filter by reunification status
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(reunification_status=status_filter)

        # Filter by search term
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                family_name__icontains=search
            ) | queryset.filter(family_code__icontains=search)

        return queryset.order_by("family_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Family.ReunificationStatus.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("search", "")

        # Statistics
        all_families = Family.objects.all()
        context["total_families"] = all_families.count()
        context["pending_families"] = all_families.filter(reunification_status="PENDING").count()
        context["partial_families"] = all_families.filter(reunification_status="PARTIAL").count()
        context["reunified_families"] = all_families.filter(reunification_status="REUNIFIED").count()

        return context


class FamilyDetailView(LoginRequiredMixin, DetailView):
    """View detailed family information with member list"""

    model = Family
    template_name = "families/family_detail.html"
    context_object_name = "family"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()

        # Get family members
        context["members"] = family.get_family_members_list()
        context["member_count"] = family.member_count
        context["checked_in_count"] = family.checked_in_count
        context["reunited_count"] = family.reunited_count
        context["missing_count"] = family.missing_count

        # Get evacuation centers
        context["centers"] = family.get_evacuation_centers()
        context["reunification_logs"] = family.reunification_logs.select_related("updated_by")[:10]

        # Calculate reunification percentage
        if family.member_count > 0:
            context["reunification_percentage"] = int(
                (family.reunited_count / family.member_count) * 100
            )
        else:
            context["reunification_percentage"] = 0

        return context


class FamilyRegistrationView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Create a new family"""

    model = Family
    form_class = FamilyRegistrationForm
    template_name = "families/family_register.html"
    success_url = reverse_lazy("family-list")
    success_message = "Family '%(family_name)s' registered successfully!"

    def test_func(self):
        return self.request.user.is_emergency_responder


class FamilyUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update family information"""

    model = Family
    form_class = FamilyUpdateForm
    template_name = "families/family_update.html"
    success_url = reverse_lazy("family-list")
    success_message = "Family information updated for %(family_name)s"

    def test_func(self):
        return self.request.user.is_emergency_responder


class FamilyReunificationUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Update family reunification status"""

    model = Family
    form_class = FamilyReunificationForm
    template_name = "families/family_reunification.html"
    success_url = reverse_lazy("family-list")
    success_message = "Reunification status updated for %(family_name)s"

    def test_func(self):
        return self.request.user.is_emergency_responder

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()
        context["members"] = family.get_family_members_list()
        context["reunification_percentage"] = (
            int((family.reunited_count / family.member_count) * 100)
            if family.member_count > 0
            else 0
        )
        context["reunification_logs"] = family.reunification_logs.select_related("updated_by")[:10]
        return context

    def form_valid(self, form):
        old_family = Family.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        notes = form.cleaned_data.get("notes", "")
        if old_family.reunification_status != self.object.reunification_status or notes:
            FamilyReunificationLog.objects.create(
                family=self.object,
                old_status=old_family.reunification_status,
                new_status=self.object.reunification_status,
                notes=notes,
                updated_by=self.request.user,
            )
        return response


class FamilyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a family"""

    model = Family
    template_name = "families/family_confirm_delete.html"
    success_url = reverse_lazy("family-list")

    def test_func(self):
        return self.request.user.is_emergency_responder

    def delete(self, request, *args, **kwargs):
        family = self.get_object()
        messages.success(request, f"Family '{family.family_name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)

