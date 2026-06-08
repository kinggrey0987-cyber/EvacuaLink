"""
Forms for mapping app with geographic constraint validation.
"""

from django import forms
from django.core.exceptions import ValidationError

from mapping.models import MapLocation, HazardZone, SafeZone
from mapping.utils import validate_barangay_coordinates


class MapLocationForm(forms.ModelForm):
    """Form for creating and editing map locations with barangay validation"""

    class Meta:
        model = MapLocation
        fields = ["name", "location_type", "latitude", "longitude", "description", "evacuation_center"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "location_type": forms.Select(attrs={"class": "form-select"}),
            "latitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.000001",
                    "placeholder": "e.g., 10.3233",
                }
            ),
            "longitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.000001",
                    "placeholder": "e.g., 122.8933",
                }
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "evacuation_center": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")

        if latitude and longitude:
            try:
                validate_barangay_coordinates(float(latitude), float(longitude))
            except ValidationError as e:
                self.add_error(None, e.message)

        return cleaned_data


class HazardZoneForm(forms.ModelForm):
    """Form for creating and editing hazard zones with barangay validation"""

    class Meta:
        model = HazardZone
        fields = ["name", "hazard_type", "latitude", "longitude", "description", "risk_level"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "hazard_type": forms.Select(attrs={"class": "form-select"}),
            "latitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.000001",
                    "placeholder": "e.g., 10.3233",
                }
            ),
            "longitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.000001",
                    "placeholder": "e.g., 122.8933",
                }
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "risk_level": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")

        if latitude and longitude:
            try:
                validate_barangay_coordinates(float(latitude), float(longitude))
            except ValidationError as e:
                self.add_error(None, e.message)

        return cleaned_data


class SafeZoneForm(forms.ModelForm):
    """Form for creating and editing safe zones with barangay validation"""

    class Meta:
        model = SafeZone
        fields = ["name", "latitude", "longitude", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "latitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.000001",
                    "placeholder": "e.g., 10.3233",
                }
            ),
            "longitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.000001",
                    "placeholder": "e.g., 122.8933",
                }
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")

        if latitude and longitude:
            try:
                validate_barangay_coordinates(float(latitude), float(longitude))
            except ValidationError as e:
                self.add_error(None, e.message)

        return cleaned_data


from mapping.models import SystemSettings

class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            "is_geofencing_enabled",
            "emergency_hotline",
            "global_announcement",
            "is_announcement_active",
            "default_map_latitude",
            "default_map_longitude",
            "default_map_zoom",
            "boundary_polygon",
        ]
        widgets = {
            "emergency_hotline": forms.TextInput(attrs={"class": "form-control"}),
            "default_map_latitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "default_map_longitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "default_map_zoom": forms.NumberInput(attrs={"class": "form-control"}),
            "boundary_polygon": forms.HiddenInput(attrs={"id": "id_boundary_polygon"}),
        }
