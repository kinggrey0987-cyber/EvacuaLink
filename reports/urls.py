from django.urls import path

from .views import (
    ReportDashboardView,
    ReportGeneratorView,
    ReportListView,
)

urlpatterns = [
    path("", ReportDashboardView.as_view(), name="report-dashboard"),
    path("generate/", ReportGeneratorView.as_view(), name="report-generate"),
    path("list/", ReportListView.as_view(), name="report-list"),
]

