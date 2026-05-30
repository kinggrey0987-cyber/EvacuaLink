from django.urls import path

from .views import (
    ReportDashboardView,
    ReportGeneratorView,
    ReportListView,
    ReportDetailView,
    ReportDeleteView,
)

urlpatterns = [
    path("", ReportDashboardView.as_view(), name="report-dashboard"),
    path("generate/", ReportGeneratorView.as_view(), name="report-generate"),
    path("list/", ReportListView.as_view(), name="report-list"),
    path("detail/<int:pk>/", ReportDetailView.as_view(), name="report-detail"),
    path("delete/<int:pk>/", ReportDeleteView.as_view(), name="report-delete"),
]


