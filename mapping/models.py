from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
import json
from shapely.geometry import Point, shape

from evacuation_centers.models import EvacuationCenter


class SystemSettings(models.Model):
    """Global system configuration settings"""

    is_geofencing_enabled = models.BooleanField(
        default=True,
        help_text="When enabled, restricts help requests to the barangay boundaries.",
    )
    emergency_hotline = models.CharField(
        max_length=100,
        default="911",
        help_text="The primary emergency contact number shown to the public.",
    )
    default_map_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=10.8286,  # Default for Talisay / Alicante roughly
        help_text="Default map center latitude.",
    )
    default_map_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=122.9733,
        help_text="Default map center longitude.",
    )
    default_map_zoom = models.IntegerField(
        default=14,
        help_text="Default map zoom level.",
    )
    global_announcement = models.TextField(
        blank=True,
        help_text="A global message displayed at the top of the site.",
    )
    is_announcement_active = models.BooleanField(
        default=False,
        help_text="Toggle to show or hide the global announcement.",
    )
    boundary_polygon = models.JSONField(
        blank=True,
        null=True,
        help_text="GeoJSON representation of the barangay boundary polygon.",
    )

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "Global System Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class MapLocation(models.Model):
    class LocationType(models.TextChoices):
        EVACUATION_CENTER = "EVACUATION_CENTER", "Evacuation Center"
        HAZARD_ZONE = "HAZARD_ZONE", "Hazard Zone"
        SAFE_ROUTE = "SAFE_ROUTE", "Safe Route"
        RELIEF_POINT = "RELIEF_POINT", "Relief Point"

    name = models.CharField(max_length=150)
    location_type = models.CharField(max_length=30, choices=LocationType.choices)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField(blank=True)
    evacuation_center = models.OneToOneField(EvacuationCenter, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.location_type})"

    @property
    def coordinates(self):
        return {"latitude": float(self.latitude), "longitude": float(self.longitude)}


class HazardZone(models.Model):
    class HazardType(models.TextChoices):
        FLOOD = "FLOOD", "Flood"
        FIRE = "FIRE", "Fire"
        LANDSLIDE = "LANDSLIDE", "Landslide"
        EARTHQUAKE = "EARTHQUAKE", "Earthquake"
        OTHER = "OTHER", "Other"

    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MODERATE = "MODERATE", "Moderate"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    name = models.CharField(max_length=150, unique=True)
    hazard_type = models.CharField(max_length=30, choices=HazardType.choices)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.MODERATE)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.risk_level}"


class SafeZone(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BarangayBoundary(models.Model):
    """Stores the geographic boundary of Barangay Alicante as a GeoJSON polygon"""

    name = models.CharField(max_length=150, unique=True, default="Barangay Alicante")
    municipality = models.CharField(max_length=150, default="EB Magalona")
    province = models.CharField(max_length=150, default="Negros Occidental")
    country = models.CharField(max_length=150, default="Philippines")

    # Store the polygon geometry as GeoJSON
    geometry = models.JSONField(
        help_text="GeoJSON Polygon geometry object with coordinates array"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "Barangay Boundaries"

    def __str__(self):
        return f"{self.name}, {self.municipality}, {self.province}"

    def contains_point(self, latitude, longitude):
        """
        Check if a point (latitude, longitude) is within this boundary polygon.

        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate

        Returns:
            bool: True if point is inside polygon, False otherwise
        """
        try:
            if not self.geometry or "coordinates" not in self.geometry:
                return False

            # Create Point object from coordinates (longitude, latitude)
            point = Point(longitude, latitude)

            # Create Polygon object from GeoJSON coordinates
            # GeoJSON format: {"type": "Polygon", "coordinates": [[[lon, lat], ...]]}
            polygon = shape(self.geometry)

            # Check if point is within polygon
            return point.within(polygon)
        except Exception as e:
            print(f"Error checking point in polygon: {e}")
            return False

    def get_bounds(self):
        """
        Get the bounding box of the polygon

        Returns:
            dict: Contains 'north', 'south', 'east', 'west' coordinates
        """
        try:
            polygon = shape(self.geometry)
            minx, miny, maxx, maxy = polygon.bounds
            return {
                'south': miny,
                'north': maxy,
                'west': minx,
                'east': maxx
            }
        except Exception as e:
            print(f"Error getting bounds: {e}")
            return None

    def get_center(self):
        """
        Get the centroid (center point) of the polygon

        Returns:
            dict: Contains 'latitude' and 'longitude' of polygon centroid
        """
        try:
            polygon = shape(self.geometry)
            centroid = polygon.centroid
            return {
                'latitude': centroid.y,
                'longitude': centroid.x
            }
        except Exception as e:
            print(f"Error getting center: {e}")
            return None
