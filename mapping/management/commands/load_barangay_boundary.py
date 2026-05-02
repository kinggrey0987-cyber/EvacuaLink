"""
Management command to load the Barangay Alicante boundary polygon from GeoJSON file.

Usage:
    python manage.py load_barangay_boundary
"""

import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from mapping.models import BarangayBoundary


class Command(BaseCommand):
    help = "Load the Barangay Alicante boundary polygon from GeoJSON file"

    def handle(self, *args, **options):
        # Use Django's BASE_DIR to construct the path
        geojson_file = settings.BASE_DIR / "mapping" / "data" / "barangay_alicante.geojson"

        if not geojson_file.exists():
            self.stdout.write(
                self.style.ERROR(f"GeoJSON file not found: {geojson_file}")
            )
            return

        try:
            with open(geojson_file, "r") as f:
                geojson_data = json.load(f)

            # Extract the first feature from the FeatureCollection
            if geojson_data.get("type") == "FeatureCollection" and geojson_data.get(
                "features"
            ):
                feature = geojson_data["features"][0]
                geometry = feature.get("geometry")
                properties = feature.get("properties", {})

                if not geometry:
                    self.stdout.write(
                        self.style.ERROR("No geometry found in GeoJSON feature")
                    )
                    return

                # Delete existing boundary (if any)
                BarangayBoundary.objects.all().delete()

                # Create new boundary
                boundary = BarangayBoundary.objects.create(
                    name=properties.get("name", "Barangay Alicante"),
                    municipality=properties.get("municipality", "EB Magalona"),
                    province=properties.get("province", "Negros Occidental"),
                    country=properties.get("country", "Philippines"),
                    geometry=geometry,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully loaded boundary: {boundary.name}, {boundary.municipality}, {boundary.province}"
                    )
                )

                # Display boundary information
                bounds = boundary.get_bounds()
                center = boundary.get_center()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Polygon bounds: North={bounds['north']:.6f}, South={bounds['south']:.6f}, "
                        f"East={bounds['east']:.6f}, West={bounds['west']:.6f}"
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Polygon center: Lat={center['latitude']:.6f}, Lon={center['longitude']:.6f}"
                    )
                )

            else:
                self.stdout.write(
                    self.style.ERROR(
                        "Invalid GeoJSON format. Expected FeatureCollection with features."
                    )
                )

        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON file: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading boundary: {e}"))
