from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, DetailView

from users.forms import CustomUserCreationForm, CustomUserChangeForm, UserLoginForm

User = get_user_model()


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


class RegisterView(UserPassesTestMixin, CreateView):
    """Handle user registration (admin only)"""

    model = User
    form_class = CustomUserCreationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy("user_list")

    def test_func(self):
        """Only admins can create new users"""
        return self.request.user.is_authenticated and self.request.user.role == User.Role.ADMIN

    def handle_no_permission(self):
        return redirect("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Register New User"
        return context


class UserListView(LoginRequiredMixin, ListView):
    """List all users (admin only)"""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        # Only admins can see all users
        if self.request.user.role == User.Role.ADMIN:
            return User.objects.all().order_by("username")
        # Other users can only see their own profile
        return User.objects.filter(pk=self.request.user.pk)


class UserDetailView(LoginRequiredMixin, DetailView):
    """Display user profile details"""

    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"

    def get_queryset(self):
        # Users can only view their own profile or admins can view anyone
        if self.request.user.role == User.Role.ADMIN:
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
        if self.request.user.role == User.Role.ADMIN:
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


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with real-time statistics"""

    template_name = "dashboard.html"

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

        # Emergency Statistics (if user has permission)
        if user.is_emergency_responder:
            context["total_help_requests"] = EmergencyHelpRequest.objects.count()
            context["pending_requests"] = EmergencyHelpRequest.objects.filter(status="PENDING").count()
            context["in_progress_requests"] = EmergencyHelpRequest.objects.filter(status="IN_PROGRESS").count()

            context["total_incidents"] = EmergencyIncident.objects.count()
            context["open_incidents"] = EmergencyIncident.objects.filter(status="OPEN").count()
            context["critical_incidents"] = EmergencyIncident.objects.filter(severity="CRITICAL").count()

        return context


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

