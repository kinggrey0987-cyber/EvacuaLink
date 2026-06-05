"""
Forms for family management and reunification tracking.
"""

from django import forms
from families.models import Family


class FamilyRegistrationForm(forms.ModelForm):
    """Form for creating a new family"""

    class Meta:
        model = Family
        fields = ["family_code", "family_name", "contact_person", "contact_number"]
        widgets = {
            "family_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., FAM-001",
                    "required": True,
                }
            ),
            "family_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Family surname",
                    "required": True,
                }
            ),
            "contact_person": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Name of contact person",
                    "required": True,
                }
            ),
            "contact_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+63 9XX XXX XXXX",
                }
            ),
        }


class FamilyUpdateForm(forms.ModelForm):
    """Form for updating family information"""

    class Meta:
        model = Family
        fields = ["family_name", "contact_person", "contact_number", "reunification_status"]
        widgets = {
            "family_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control"}),
            "reunification_status": forms.Select(attrs={"class": "form-select"}),
        }


class FamilyReunificationForm(forms.ModelForm):
    """Form for updating family reunification status"""

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Record where members were found, who confirmed reunification, or what remains unresolved.",
            }
        ),
    )

    class Meta:
        model = Family
        fields = ["reunification_status"]
        widgets = {
            "reunification_status": forms.Select(attrs={"class": "form-select"}),
        }


class FamilyLegacyForm(forms.ModelForm):
    """Legacy form - kept for backwards compatibility"""

    class Meta:
        model = Family
        fields = ["family_code", "family_name", "contact_person", "contact_number", "reunification_status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

