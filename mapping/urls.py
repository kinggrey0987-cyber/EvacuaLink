from django.urls import path

from .views import (
    PublicMapView,
    AdminMapView,
    MapLocationListView,
    MapLocationCreateView,
    MapLocationUpdateView,
    HazardZoneListView,
    HazardZoneCreateView,
    HazardZoneUpdateView,
    HazardZoneDeleteView,
    SafeZoneListView,
    SafeZoneCreateView,
    SafeZoneUpdateView,
    SafeZoneDeleteView,
    MapAPIView,
)

urlpatterns = [
    # Public Maps
    path("", PublicMapView.as_view(), name="public-map"),
    path("admin/", AdminMapView.as_view(), name="admin-map"),

    # API
    path("api/locations/", MapAPIView.as_view(), name="map-api-locations"),

    # Map Locations
    path("locations/", MapLocationListView.as_view(), name="map-location-list"),
    path("locations/create/", MapLocationCreateView.as_view(), name="map-location-create"),
    path("locations/<int:pk>/edit/", MapLocationUpdateView.as_view(), name="map-location-edit"),

    # Hazard Zones
    path("hazard-zones/", HazardZoneListView.as_view(), name="hazard-zone-list"),
    path("hazard-zones/create/", HazardZoneCreateView.as_view(), name="hazard-zone-create"),
    path("hazard-zones/<int:pk>/edit/", HazardZoneUpdateView.as_view(), name="hazard-zone-edit"),
    path("hazard-zones/<int:pk>/delete/", HazardZoneDeleteView.as_view(), name="hazard-zone-delete"),

    # Safe Zones
    path("safe-zones/", SafeZoneListView.as_view(), name="safe-zone-list"),
    path("safe-zones/create/", SafeZoneCreateView.as_view(), name="safe-zone-create"),
    path("safe-zones/<int:pk>/edit/", SafeZoneUpdateView.as_view(), name="safe-zone-edit"),
    path("safe-zones/<int:pk>/delete/", SafeZoneDeleteView.as_view(), name="safe-zone-delete"),
]

