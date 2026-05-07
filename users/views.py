from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, DetailView

from users.forms import CustomUserCreationForm, CustomUserChangeForm, UserLoginForm

User = get_user_model()


class PublicLandingPageView(TemplateView):
    """Public landing page - no login required. Shows safety map and help request button for citizens."""

    template_name = "public/landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get map data for public view
        from mapping.models import HazardZone, SafeZone, BarangayBoundary
        from evacuation_centers.models import EvacuationCenter
        from mapping.utils import get_barangay_boundary_geojson, get_barangay_center_and_bounds, get_zoom_level_for_bounds

        # Get all active locations
        evacuation_centers = list(
            EvacuationCenter.objects.all().values("id", "name", "latitude", "longitude", "address")
        )

        hazard_zones = list(
            HazardZone.objects.all().values("id", "name", "latitude", "longitude", "hazard_type", "risk_level", "description")
        )

        safe_zones = list(
            SafeZone.objects.all().values("id", "name", "latitude", "longitude", "description")
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

        return context




class LoginView(View):
    """Handle user login"""

    template_name = "auth/login.html"
    form_class = UserLoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                next_url = request.GET.get("next", "dashboard")
                return redirect(next_url)
            else:
                form.add_error(None, "Invalid username or password.")

        return render(request, self.template_name, {"form": form})


class LogoutView(LoginRequiredMixin, View):
    """Handle user logout"""

    def get(self, request):
        logout(request)
        return redirect("login")


class OperationalDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Main operational dashboard for emergency responders and staff.
    TECHNICAL_ADMIN users are redirected to Django admin instead.
    """

    template_name = "dashboard.html"

    def test_func(self):
        """Only operational staff (not technical admins) can access this"""
        return not self.request.user.is_technical_admin

    def handle_no_permission(self):
        """Redirect technical admins to admin panel"""
        if self.request.user.is_authenticated and self.request.user.is_technical_admin:
            return redirect("evacualink_admin:index")
        return redirect("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user"] = user
        context["user_role"] = user.get_role_display()
        context["is_technical_admin"] = user.is_technical_admin
        context["is_operational_admin"] = user.is_operational_admin

        # Import models for statistics
        from evacuees.models import Evacuee
        from families.models import Family
        from evacuation_centers.models import EvacuationCenter
        from emergency.models import EmergencyHelpRequest, EmergencyIncident

        # General Statistics
        context["total_users"] = User.objects.count()
        context["total_evacuees"] = Evacuee.objects.count()
        context["total_families"] = Family.objects.count()
        context["total_centers"] = EvacuationCenter.objects.count()

        # Evacuee Status Statistics
        context["evacuees_registered"] = Evacuee.objects.filter(status="REGISTERED").count()
        context["evacuees_checked_in"] = Evacuee.objects.filter(status="CHECKED_IN").count()
        context["evacuees_reunited"] = Evacuee.objects.filter(status="REUNITED").count()
        context["evacuees_missing"] = Evacuee.objects.filter(status="MISSING").count()
        context["evacuees_special_needs"] = Evacuee.objects.filter(special_needs=True).count()

        # Family Statistics
        context["families_pending"] = Family.objects.filter(reunification_status="PENDING").count()
        context["families_partial"] = Family.objects.filter(reunification_status="PARTIAL").count()
        context["families_reunified"] = Family.objects.filter(reunification_status="REUNIFIED").count()

        # Center Occupancy
        context["centers_open"] = EvacuationCenter.objects.filter(status="OPEN").count()
        context["centers_full"] = EvacuationCenter.objects.filter(status="FULL").count()
        context["centers_closed"] = EvacuationCenter.objects.filter(status="CLOSED").count()

        # Emergency Statistics
        context["total_help_requests"] = EmergencyHelpRequest.objects.count()
        context["pending_requests"] = EmergencyHelpRequest.objects.filter(status="PENDING").count()
        context["in_progress_requests"] = EmergencyHelpRequest.objects.filter(status="IN_PROGRESS").count()

        context["total_incidents"] = EmergencyIncident.objects.count()
        context["open_incidents"] = EmergencyIncident.objects.filter(status="OPEN").count()
        context["critical_incidents"] = EmergencyIncident.objects.filter(severity="CRITICAL").count()

        return context


class RegisterView(UserPassesTestMixin, CreateView):
    """Handle user registration (operational admin only)"""

    model = User
    form_class = CustomUserCreationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy("user_list")

    def test_func(self):
        """Only operational admins can create new users"""
        return (
            self.request.user.is_authenticated
            and self.request.user.is_operational_admin
        )

    def handle_no_permission(self):
        return redirect("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Register New User"
        return context


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all users (operational admin only)"""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def test_func(self):
        """Only operational admins can view user list"""
        return self.request.user.is_operational_admin

    def get_queryset(self):
        return User.objects.all().order_by("username")


class UserDetailView(LoginRequiredMixin, DetailView):
    """Display user profile details"""

    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"

    def get_queryset(self):
        # Users can only view their own profile or admins can view anyone
        if self.request.user.is_operational_admin:
            return User.objects.all()
        return User.objects.filter(pk=self.request.user.pk)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """Update user information"""

    model = User
    form_class = CustomUserChangeForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("dashboard")

    def get_queryset(self):
        # Users can only update their own profile or admins can update anyone
        if self.request.user.is_operational_admin:
            return User.objects.all()
        return User.objects.filter(pk=self.request.user.pk)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        # If user_id is in URL, use that; otherwise use current user
        user_id = self.kwargs.get("pk")
        if user_id:
            return queryset.get(pk=user_id)
        return self.request.user


class DashboardView(OperationalDashboardView):
    """Alias for backward compatibility"""
    pass


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""

    template_name = "users/profile.html"

    def render_to_response(self, context, **response_kwargs):
        user = self.request.user
        return JsonResponse(
            {
                "username": user.username,
                "email": user.email,
                "full_name": user.get_full_name(),
                "role": user.role,
                "phone_number": user.phone_number,
            }
        )


