"""
Forms for emergency management system.
"""

from django import forms
from django.core.exceptions import ValidationError

from emergency.models import EmergencyHelpRequest, EmergencyIncident
from mapping.utils import validate_barangay_coordinates


class EmergencyHelpRequestForm(forms.ModelForm):
    """Form for public emergency help requests with geographic validation"""

    class Meta:
        model = EmergencyHelpRequest
        fields = ["requester_name", "contact_number", "location_description", "latitude", "longitude", "message"]
        widgets = {
            "requester_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your full name",
                    "required": True,
                }
            ),
            "contact_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+63 9XX XXX XXXX",
                    "required": True,
                }
            ),
            "location_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Describe your location (e.g., near the school, by the main road)",
                    "required": True,
                }
            ),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe your emergency situation and what help you need",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["requester_name"].label = "Your Name"
        self.fields["contact_number"].label = "Contact Number"
        self.fields["location_description"].label = "Location Description"
        self.fields["latitude"].label = "Latitude"
        self.fields["longitude"].label = "Longitude"
        self.fields["message"].label = "Emergency Message"

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


class EmergencyHelpRequestStatusForm(forms.ModelForm):
    """Form for updating help request status (admin only)"""

    class Meta:
        model = EmergencyHelpRequest
        fields = ["status", "resolved_at"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "resolved_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].label = "Request Status"
        self.fields["resolved_at"].label = "Resolved At"
        self.fields["resolved_at"].required = False


class EmergencyIncidentForm(forms.ModelForm):
    """Form for creating and updating emergency incidents (admin/responders only)"""

    class Meta:
        model = EmergencyIncident
        fields = ["title", "description", "location", "severity", "status", "evacuation_center", "resolved_at"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "severity": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "evacuation_center": forms.Select(attrs={"class": "form-select"}),
            "resolved_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resolved_at"].required = False
        self.fields["evacuation_center"].required = False
