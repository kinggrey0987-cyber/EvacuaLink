"""
Utility functions for mapping and geographic operations.
"""

from django.core.exceptions import ValidationError
from shapely.geometry import Point, shape
from mapping.models import BarangayBoundary


def is_within_barangay_boundary(latitude, longitude):
    """
    Check if a point (latitude, longitude) is within Barangay Alicante boundary.

    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate

    Returns:
        bool: True if point is inside barangay polygon, False otherwise
    """
    try:
        from mapping.models import SystemSettings, BarangayBoundary
        settings = SystemSettings.get_settings()
        if not settings.is_geofencing_enabled:
            return True

        if settings.boundary_polygon:
            polygon = shape(settings.boundary_polygon)
            return Point(longitude, latitude).within(polygon)

        boundary = BarangayBoundary.objects.first()
        if not boundary:
            # If boundary doesn't exist, accept the coordinates
            return True
        return boundary.contains_point(latitude, longitude)
    except Exception as e:
        print(f"Error checking point in boundary: {e}")
        return False


def validate_barangay_coordinates(latitude, longitude):
    """
    Validate that coordinates are within Barangay Alicante.
    Raises ValidationError if outside boundary.

    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate

    Raises:
        ValidationError: If coordinates are outside barangay boundary
    """
    if not is_within_barangay_boundary(latitude, longitude):
        raise ValidationError(
            "Location coordinates must be within Barangay Alicante, EB Magalona, Negros Occidental."
        )


def get_barangay_boundary_geojson():
    """
    Get the Barangay Alicante boundary as GeoJSON.

    Returns:
        dict: GeoJSON geometry object or None if boundary doesn't exist
    """
    try:
        from mapping.models import SystemSettings, BarangayBoundary
        settings = SystemSettings.get_settings()
        if settings.boundary_polygon:
            return settings.boundary_polygon

        boundary = BarangayBoundary.objects.first()
        if boundary and boundary.geometry:
            return boundary.geometry
        return None
    except Exception as e:
        print(f"Error getting boundary GeoJSON: {e}")
        return None


def get_barangay_center_and_bounds():
    """
    Get the center point and bounds of Barangay Alicante.

    Returns:
        dict: Contains 'center' and 'bounds' with latitude/longitude values
    """
    try:
        from mapping.models import SystemSettings, BarangayBoundary
        settings = SystemSettings.get_settings()
        
        default_data = {
            "center": {
                "latitude": float(settings.default_map_latitude),
                "longitude": float(settings.default_map_longitude)
            },
            "bounds": {
                "north": float(settings.default_map_latitude) + 0.015,
                "south": float(settings.default_map_latitude) - 0.015,
                "east": float(settings.default_map_longitude) + 0.015,
                "west": float(settings.default_map_longitude) - 0.015,
            },
        }

        if settings.boundary_polygon:
            polygon = shape(settings.boundary_polygon)
            minx, miny, maxx, maxy = polygon.bounds
            centroid = polygon.centroid
            return {
                "center": {
                    "latitude": centroid.y,
                    "longitude": centroid.x
                },
                "bounds": {
                    "north": maxy + 0.02,
                    "south": miny - 0.02,
                    "east": maxx + 0.02,
                    "west": minx - 0.02,
                }
            }

        boundary = BarangayBoundary.objects.first()
        if not boundary:
            return default_data

        return {
            "center": boundary.get_center(),
            "bounds": boundary.get_bounds(),
        }
    except Exception as e:
        print(f"Error getting barangay center and bounds: {e}")
        try:
            from mapping.models import SystemSettings
            settings = SystemSettings.get_settings()
            return {
                "center": {
                    "latitude": float(settings.default_map_latitude),
                    "longitude": float(settings.default_map_longitude)
                },
                "bounds": {
                    "north": float(settings.default_map_latitude) + 0.015,
                    "south": float(settings.default_map_latitude) - 0.015,
                    "east": float(settings.default_map_longitude) + 0.015,
                    "west": float(settings.default_map_longitude) - 0.015,
                },
            }
        except:
            return {
                "center": {"latitude": 10.3233, "longitude": 122.8933},
                "bounds": {
                    "north": 10.3550,
                    "south": 10.3000,
                    "east": 122.9100,
                    "west": 122.8700,
                },
            }


def get_zoom_level_for_bounds():
    """
    Get appropriate map zoom level for displaying barangay.

    Returns:
        int: Zoom level (13-14 for barangay view)
    """
    try:
        from mapping.models import SystemSettings
        return SystemSettings.get_settings().default_map_zoom
    except:
        return 13


class BarangayBoundaryValidator:
    """Validator for ensuring coordinates are within barangay boundary"""

    def __init__(self, latitude_field_name="latitude", longitude_field_name="longitude"):
        self.latitude_field_name = latitude_field_name
        self.longitude_field_name = longitude_field_name

    def __call__(self, value):
        """
        Validate a dictionary containing latitude and longitude.

        Args:
            value (dict): Dictionary with 'latitude' and 'longitude' keys
        """
        if isinstance(value, dict):
            lat = value.get(self.latitude_field_name)
            lon = value.get(self.longitude_field_name)
            if lat and lon:
                validate_barangay_coordinates(float(lat), float(lon))
