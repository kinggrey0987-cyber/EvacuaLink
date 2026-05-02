"""
Utility functions for mapping and geographic operations.
"""

from django.core.exceptions import ValidationError
from shapely.geometry import Point
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
        boundary = BarangayBoundary.objects.first()
        if not boundary:
            # Default coordinates if boundary doesn't exist
            return {
                "center": {"latitude": 10.3233, "longitude": 122.8933},
                "bounds": {
                    "north": 10.3550,
                    "south": 10.3000,
                    "east": 122.9100,
                    "west": 122.8700,
                },
            }

        return {
            "center": boundary.get_center(),
            "bounds": boundary.get_bounds(),
        }
    except Exception as e:
        print(f"Error getting barangay center and bounds: {e}")
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
    Get appropriate Leaflet zoom level for displaying barangay.

    Returns:
        int: Zoom level (13-14 for barangay view)
    """
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
