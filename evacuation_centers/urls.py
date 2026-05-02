from django.urls import path

from .views import (
    EvacuationCenterCreateView,
    EvacuationCenterDeleteView,
    EvacuationCenterDetailView,
    EvacuationCenterListView,
    EvacuationCenterUpdateView,
)

urlpatterns = [
    path("", EvacuationCenterListView.as_view(), name="evacuation-center-list"),
    path("add/", EvacuationCenterCreateView.as_view(), name="evacuation-center-add"),
    path("<int:pk>/", EvacuationCenterDetailView.as_view(), name="evacuation-center-detail"),
    path("<int:pk>/edit/", EvacuationCenterUpdateView.as_view(), name="evacuation-center-edit"),
    path("<int:pk>/delete/", EvacuationCenterDeleteView.as_view(), name="evacuation-center-delete"),
]
