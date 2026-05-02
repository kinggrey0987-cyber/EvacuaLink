from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    RegisterView,
    DashboardView,
    ProfileView,
    UserListView,
    UserDetailView,
    UserUpdateView,
)

urlpatterns = [
    # Authentication
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),

    # Dashboard and Profile
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("profile/", ProfileView.as_view(), name="user-profile"),

    # User Management
    path("list/", UserListView.as_view(), name="user_list"),
    path("<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
]
