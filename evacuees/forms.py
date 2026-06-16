"""
Forms for evacuee management with validation for special needs.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from evacuees.models import Evacuee, TransferRecord
from families.models import Family
from evacuation_centers.models import EvacuationCenter


class EvacueeRegistrationForm(forms.ModelForm):
    """Form for registering new evacuees"""

    family = forms.ModelChoiceField(
        queryset=Family.objects.all().order_by("family_name"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Family",
        required=False,
    )

    class Meta:
        model = Evacuee
        fields = [
            "first_name",
            "last_name",
            "age",
            "gender",
            "family",
            "special_needs",
            "special_needs_description",
            "medical_condition",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                    "required": True,
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                    "required": True,
                }
            ),
            "age": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "130",
                    "required": True,
                    "oninput": "this.value = this.value.replace(/[^0-9]/g, '')",
                }
            ),
            "gender": forms.Select(attrs={"class": "form-select", "required": True}),
            "special_needs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "special_needs_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe special needs (e.g., wheelchair access, medical equipment)",
                }
            ),
            "medical_condition": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Medical conditions, allergies, medications",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        special_needs = cleaned_data.get("special_needs")
        special_needs_description = cleaned_data.get("special_needs_description", "").strip()

        if special_needs and not special_needs_description:
            raise ValidationError(
                "Please describe the special needs when marking an evacuee as having special needs."
            )

        return cleaned_data


class EvacueeAssignmentForm(forms.Form):
    """Form for assigning evacuees to centers"""

    evacuation_center = forms.ModelChoiceField(
        queryset=EvacuationCenter.objects.filter(status="OPEN").order_by("name"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Evacuation Center",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update center choices to show capacity info
        centers = [center for center in EvacuationCenter.objects.filter(status="OPEN").order_by("name") if not center.is_full()]
        choices = [(c.id, f"{c.name} ({c.current_occupancy}/{c.capacity})") for c in centers]
        self.fields["evacuation_center"].choices = choices


class EvacueeStatusForm(forms.ModelForm):
    """Form for updating evacuee status"""

    class Meta:
        model = Evacuee
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class EvacueeUpdateForm(forms.ModelForm):
    """Form for updating evacuee information"""

    class Meta:
        model = Evacuee
        fields = [
            "first_name",
            "last_name",
            "age",
            "gender",
            "special_needs",
            "special_needs_description",
            "medical_condition",
            "status",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "age": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "130",
                    "oninput": "this.value = this.value.replace(/[^0-9]/g, '')",
                }
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "special_needs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "special_needs_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "medical_condition": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        special_needs = cleaned_data.get("special_needs")
        special_needs_description = cleaned_data.get("special_needs_description", "").strip()

        if special_needs and not special_needs_description:
            raise ValidationError(
                "Please describe the special needs when marking an evacuee as having special needs."
            )

        return cleaned_data


class EvacueeTransferForm(forms.ModelForm):
    """Form for transferring evacuee between centers"""

    from_center = forms.ModelChoiceField(
        queryset=EvacuationCenter.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="From Center",
        required=True,
    )

    to_center = forms.ModelChoiceField(
        queryset=EvacuationCenter.objects.filter(status="OPEN"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="To Center",
        required=True,
    )

    class Meta:
        model = TransferRecord
        fields = ["from_center", "to_center", "transfer_date", "reason"]
        widgets = {
            "transfer_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Why is the evacuee being transferred?",
                }
            ),
        }

    def __init__(self, evacuee=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evacuee = evacuee

        # Pre-fill transfer_date with current time
        if not self.initial.get("transfer_date"):
            self.initial["transfer_date"] = timezone.now()

        # Pre-fill from_center if evacuee is provided
        if evacuee and evacuee.evacuation_center:
            self.initial["from_center"] = evacuee.evacuation_center
            self.fields["from_center"].queryset = EvacuationCenter.objects.filter(pk=evacuee.evacuation_center_id)
            self.fields["from_center"].disabled = True

        if evacuee and evacuee.evacuation_center_id:
            self.fields["to_center"].queryset = EvacuationCenter.objects.filter(status="OPEN").exclude(
                pk=evacuee.evacuation_center_id
            ).order_by("name")
        else:
            self.fields["to_center"].queryset = EvacuationCenter.objects.filter(status="OPEN").order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        from_center = cleaned_data.get("from_center")
        to_center = cleaned_data.get("to_center")

        if from_center and to_center and from_center.id == to_center.id:
            raise ValidationError(
                "The destination center must be different from the origin center."
            )

        if to_center and to_center.is_full():
            raise ValidationError("The destination center is already full.")

        return cleaned_data


class EvacueeLegacyForm(forms.ModelForm):
    """Legacy form - kept for backwards compatibility"""

    class Meta:
        model = Evacuee
        fields = [
            "first_name",
            "last_name",
            "age",
            "gender",
            "family",
            "evacuation_center",
            "special_needs",
            "special_needs_description",
            "medical_condition",
            "status",
        ]
        widgets = {
            "special_needs_description": forms.Textarea(attrs={"rows": 3}),
            "medical_condition": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "special_needs":
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")

