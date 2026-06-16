"""
Forms for family management and reunification tracking.
"""

from django import forms
from families.models import Family
from evacuees.models import Evacuee


class FamilyRegistrationForm(forms.ModelForm):
    """Form for creating a new family"""

    contact_person = forms.ModelChoiceField(
        queryset=Evacuee.objects.filter(family__isnull=True).order_by("last_name", "first_name"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Contact Person (Independent Evacuee)",
        required=False,
    )

    class Meta:
        model = Family
        fields = ["family_name", "contact_person", "contact_number"]
        widgets = {
            "family_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Family surname",
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
            "contact_person": forms.Select(attrs={"class": "form-select"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control"}),
            "reunification_status": forms.Select(attrs={"class": "form-control"}),
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

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("reunification_status")
        
        if status == Family.ReunificationStatus.REUNIFIED:
            family = self.instance
            if not family.is_fully_reunified:
                raise forms.ValidationError("Cannot mark as Reunified: Not all members are individually marked as Reunited.")
            
            centers = family.get_evacuation_centers()
            if len(centers) > 1:
                raise forms.ValidationError("Cannot mark as Reunified: Members are physically located in multiple different evacuation centers.")
            
        return cleaned_data


class FamilyLegacyForm(forms.ModelForm):
    """Legacy form - kept for backwards compatibility"""

    class Meta:
        model = Family
        fields = ["family_code", "family_name", "contact_person", "contact_number", "reunification_status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
