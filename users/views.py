import hmac
import random
import secrets
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, AdminPasswordChangeForm
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, DetailView, FormView
from django.utils import timezone

from users.forms import CustomUserCreationForm, CustomUserChangeForm, UserLoginForm
from users.security import (
    get_client_ip,
    get_rate_limit_key,
    is_rate_limited,
    record_failed_attempt,
    reset_failed_attempts,
)

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

        boundary = BarangayBoundary.objects.first()

        def inside_boundary(item):
            if not boundary:
                return True
            return boundary.contains_point(float(item["latitude"]), float(item["longitude"]))

        evacuation_centers = [center for center in evacuation_centers if inside_boundary(center)]
        hazard_zones = [zone for zone in hazard_zones if inside_boundary(zone)]
        safe_zones = [zone for zone in safe_zones if inside_boundary(zone)]

        from mapping.models import SystemSettings
        # OOP_PRESENTATION: ENCAPSULATION (Calling the encapsulated method without needing to know the database query)
        settings_obj = SystemSettings.get_settings()

        context["emergency_hotline"] = settings_obj.emergency_hotline
        context["evacuation_centers"] = evacuation_centers
        context["hazard_zones"] = hazard_zones
        context["safe_zones"] = safe_zones
        context["boundary_geojson"] = boundary_geojson
        context["map_center"] = location_data["center"]
        context["map_bounds"] = location_data["bounds"]
        context["zoom_level"] = get_zoom_level_for_bounds()
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["landing_map_payload"] = {
            "center": {
                "latitude": float(location_data["center"].get("latitude", 10.3233)),
                "longitude": float(location_data["center"].get("longitude", 122.8933)),
            },
            "bounds": {
                "north": float(location_data["bounds"].get("north", 10.3550)),
                "south": float(location_data["bounds"].get("south", 10.3000)),
                "east": float(location_data["bounds"].get("east", 122.9100)),
                "west": float(location_data["bounds"].get("west", 122.8700)),
            },
            "boundary": boundary_geojson,
            "evacuationCenters": [{**c, "latitude": float(c["latitude"]), "longitude": float(c["longitude"])} for c in evacuation_centers],
            "hazardZones": [{**z, "latitude": float(z["latitude"]), "longitude": float(z["longitude"])} for z in hazard_zones],
            "safeZones": [{**z, "latitude": float(z["latitude"]), "longitude": float(z["longitude"])} for z in safe_zones],
            "isGeofencingEnabled": settings_obj.is_geofencing_enabled,
        }

        return context




class LoginView(View):
    """Handle user login with brute force protection and rate limiting"""

    template_name = "auth/login.html"
    form_class = UserLoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        ip = get_client_ip(request)
        raw_username = request.POST.get("username", "").strip()
        ip_key = get_rate_limit_key("login_ip", ip)
        user_key = get_rate_limit_key("login_user", raw_username)

        # Brute force protection: check rate limits (10 attempts per IP, 5 attempts per user / 5 minutes)
        if is_rate_limited(ip_key, max_attempts=10) or is_rate_limited(user_key, max_attempts=5):
            form = self.form_class(request.POST)
            form.add_error(
                None,
                "Too many failed login attempts. For security, please wait 5 minutes before trying again.",
            )
            return render(request, self.template_name, {"form": form}, status=429)

        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Reset rate limits on successful password verification
                reset_failed_attempts(ip_key)
                reset_failed_attempts(user_key)

                if not user.email:
                    # Fallback for old accounts without email
                    login(request, user)
                    next_url = request.GET.get("next", "dashboard")
                    if not url_has_allowed_host_and_scheme(
                        next_url,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    ):
                        next_url = "dashboard"
                    return redirect(next_url)

                # Generate cryptographically secure 6-digit OTP
                otp_code = f"{secrets.randbelow(1000000):06d}"
                request.session["pending_user_id"] = user.id
                request.session["otp_code"] = otp_code
                request.session["otp_timestamp"] = timezone.now().timestamp()
                request.session["otp_attempts"] = 0
                request.session["next_url"] = request.GET.get("next", "dashboard")

                # Send email
                try:
                    html_message = f"""
                    <html>
                        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f7f6; padding: 40px 20px; color: #333; margin: 0;">
                            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; padding: 40px 30px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.05); text-align: center;">
                                <h2 style="color: #0d6efd; margin-top: 0; font-size: 24px; font-weight: 600;">EvacuaLink Security</h2>
                                <p style="font-size: 16px; color: #555; line-height: 1.5; margin-bottom: 30px;">
                                    Please use the verification code below to sign in to your EvacuaLink dashboard.
                                </p>
                                
                                <div style="margin: 0 0 30px 0; padding: 25px; background-color: #f8f9fa; border-radius: 8px; border: 2px dashed #0d6efd;">
                                    <h1 style="font-size: 54px; margin: 0; letter-spacing: 8px; color: #212529; font-weight: 700;">{otp_code}</h1>
                                </div>
                                
                                <p style="font-size: 14px; color: #777;">This code will securely expire in <strong>10 minutes</strong>.</p>
                                
                                <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;" />
                                <p style="font-size: 12px; color: #999; line-height: 1.4;">
                                    If you didn't request this code, your password might be compromised. You can safely ignore this email if you aren't trying to log in.
                                </p>
                            </div>
                        </body>
                    </html>
                    """
                    
                    send_mail(
                        "EvacuaLink Dashboard - Your Login Verification Code",
                        f"Your login verification code is: {otp_code}\n\nThis code will expire in 10 minutes.",
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                        html_message=html_message,
                    )
                except Exception as e:
                    print(f"Error sending email: {e}")

                return redirect("otp_verify")
            else:
                record_failed_attempt(ip_key, timeout=300)
                record_failed_attempt(user_key, timeout=300)
                form.add_error(None, "Invalid username or password.")
        else:
            record_failed_attempt(ip_key, timeout=300)

        return render(request, self.template_name, {"form": form})


class OTPVerificationView(View):
    """Handle OTP verification after initial login with attempt limiting and timing-attack resistance"""

    template_name = "auth/otp_verify.html"

    def get(self, request):
        if "pending_user_id" not in request.session:
            return redirect("login")
        return render(request, self.template_name)

    def post(self, request):
        if "pending_user_id" not in request.session:
            return redirect("login")

        # Track and limit OTP attempts to prevent brute force attack on 6-digit codes
        attempts = request.session.get("otp_attempts", 0) + 1
        request.session["otp_attempts"] = attempts

        if attempts > 5:
            # Revoke OTP and purge session on exceeding maximum attempts
            for key in ["pending_user_id", "otp_code", "otp_timestamp", "otp_attempts", "next_url"]:
                request.session.pop(key, None)
            return render(
                request,
                self.template_name,
                {
                    "error": "Too many invalid OTP attempts. For security, this verification code has been revoked. Please log in again."
                },
                status=429,
            )

        submitted_otp = request.POST.get("otp_code", "").strip()
        stored_otp = request.session.get("otp_code")
        timestamp = request.session.get("otp_timestamp", 0)

        # Check expiration (10 minutes)
        if timezone.now().timestamp() - timestamp > 600:
            for key in ["pending_user_id", "otp_code", "otp_timestamp", "otp_attempts", "next_url"]:
                request.session.pop(key, None)
            return render(request, self.template_name, {"error": "OTP has expired. Please log in again."})

        # Constant-time comparison to prevent timing attacks
        if stored_otp and hmac.compare_digest(submitted_otp, stored_otp):
            user_id = request.session.get("pending_user_id")
            user = User.objects.get(id=user_id)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            next_url = request.session.get("next_url", "dashboard")
            if not url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                next_url = "dashboard"

            # Clean up session
            for key in ["pending_user_id", "otp_code", "otp_timestamp", "otp_attempts", "next_url"]:
                request.session.pop(key, None)

            return redirect(next_url)
        else:
            remaining = max(0, 5 - attempts)
            return render(
                request,
                self.template_name,
                {"error": f"Invalid OTP code. {remaining} attempt(s) remaining."},
            )


class LogoutView(LoginRequiredMixin, View):
    """Handle user logout"""

    def get(self, request):
        logout(request)
        return redirect("login")


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Read-only operational dashboard for ADMIN users.
    Shows overview metrics and report access only (no add/edit/delete actions).
    """

    template_name = "dashboards/admin_dashboard.html"

    def test_func(self):
        """Only operational admins can access this"""
        return self.request.user.is_operational_admin

    def handle_no_permission(self):
        return redirect("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user"] = user
        context["user_role"] = user.get_role_display()

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

        # Mini Safety Map Data
        from mapping.models import HazardZone, SafeZone, MapLocation
        from evacuation_centers.models import EvacuationCenter
        from mapping.utils import get_barangay_boundary_geojson, get_barangay_center_and_bounds
        
        # OOP_PRESENTATION: ABSTRACTION (Django ORM abstracts away complex SQL queries)
        evacuation_centers = list(EvacuationCenter.objects.filter(status__in=["OPEN", "FULL"]).values("id", "name", "latitude", "longitude", "address"))
        hazard_zones = list(HazardZone.objects.all().values("id", "name", "latitude", "longitude", "hazard_type", "risk_level", "description"))
        safe_zones = list(SafeZone.objects.all().values("id", "name", "latitude", "longitude", "description"))
        
        location_data = get_barangay_center_and_bounds()
        context["map_center"] = location_data["center"]
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["public_map_payload"] = {
            "center": location_data["center"],
            "bounds": location_data["bounds"],
            "boundary": get_barangay_boundary_geojson(),
            "evacuationCenters": evacuation_centers,
            "hazardZones": hazard_zones,
            "safeZones": safe_zones,
        }

        return context


class StaffDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Full operational dashboard for STAFF users.
    Shows all metrics with action buttons for managing evacuees, families, centers, zones, and incidents.
    """

    template_name = "dashboards/staff_dashboard.html"

    def test_func(self):
        """Only emergency responders (STAFF) can access this"""
        return self.request.user.is_emergency_responder

    def handle_no_permission(self):
        return redirect("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user"] = user
        context["user_role"] = user.get_role_display()

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


class OperationalDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Router view that redirects users to role-specific dashboards.
    TECHNICAL_ADMIN users are redirected to account/system administration.
    """

    def test_func(self):
        """Only operational staff (not technical admins) can access this"""
        return not self.request.user.is_technical_admin

    def handle_no_permission(self):
        """Redirect technical admins to account management."""
        if self.request.user.is_authenticated and self.request.user.is_technical_admin:
            return redirect("user_list")
        return redirect("login")

    def get(self, request, *args, **kwargs):
        """Route to appropriate dashboard based on user role"""
        user = request.user

        if user.is_operational_admin:
            return redirect("admin-dashboard")
        elif user.is_emergency_responder:
            return redirect("staff-dashboard")
        else:
            return redirect("login")


class RegisterView(UserPassesTestMixin, CreateView):
    """Handle user registration (technical admin only)"""

    model = User
    form_class = CustomUserCreationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy("user_list")

    def test_func(self):
        """Only technical admins can create new users"""
        return (
            self.request.user.is_authenticated
            and self.request.user.is_technical_admin
        )

    def handle_no_permission(self):
        return redirect("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Register New User"
        return context


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all users (technical admin only)"""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 5

    def test_func(self):
        """Only technical admins can view user list"""
        return self.request.user.is_technical_admin

    def get_queryset(self):
        return User.objects.all().order_by("-id")


class UserDetailView(LoginRequiredMixin, DetailView):
    """Display user profile details"""

    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"

    def get_queryset(self):
        # Users can only view their own profile or admins can view anyone
        if self.request.user.is_technical_admin:
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
        if self.request.user.is_technical_admin:
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs


class DashboardView(OperationalDashboardView):
    """Alias for backward compatibility"""
    pass


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""

    template_name = "users/profile.html"


class UserPasswordChangeView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Change user password with strict ownership and technical admin authorization checks"""
    template_name = "users/password_change.html"

    def test_func(self):
        user_id = self.kwargs.get("pk")
        if not user_id:
            return True
        return self.request.user.is_technical_admin or self.request.user.pk == user_id

    def handle_no_permission(self):
        return HttpResponseForbidden("You do not have permission to change this user's password.")

    def get_form_class(self):
        user_id = self.kwargs.get("pk")
        if self.request.user.is_technical_admin and user_id and user_id != self.request.user.pk:
            return AdminPasswordChangeForm
        return PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_id = self.kwargs.get("pk")
        if user_id:
            kwargs['user'] = get_object_or_404(User, pk=user_id)
        else:
            kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        # Keep user logged in if they changed their own password
        if user == self.request.user:
            update_session_auth_hash(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        user_id = self.kwargs.get("pk")
        if user_id:
            return reverse("user_edit", kwargs={"pk": user_id})
        return reverse("dashboard")
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("pk")
        if user_id:
            context['target_user'] = get_object_or_404(User, pk=user_id)
        else:
            context['target_user'] = self.request.user
        return context
