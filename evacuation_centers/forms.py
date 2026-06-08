from django import forms

from .models import EvacuationCenter


class EvacuationCenterForm(forms.ModelForm):
    class Meta:
        model = EvacuationCenter
        fields = ["name", "address", "latitude", "longitude", "capacity", "current_occupancy", "status"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        
        self.fields["status"].help_text = "Note: 'Open' and 'Full' are automatically managed based on current occupancy vs capacity."
        self.fields["current_occupancy"].help_text = "Usually automatically updated when evacuees are checked in or out."

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        capacity = cleaned_data.get("capacity")
        current_occupancy = cleaned_data.get("current_occupancy")

        if capacity is not None and current_occupancy is not None and status:
            if status == "OPEN" and current_occupancy >= capacity:
                self.add_error("status", f"Action Denied: You cannot manually set this center to 'Open' because its current occupancy ({current_occupancy}) has reached or exceeded its capacity ({capacity}).")
            elif status == "FULL" and current_occupancy < capacity:
                self.add_error("status", f"Action Denied: You cannot manually set this center to 'Full' because it still has available space (Occupancy: {current_occupancy} / Capacity: {capacity}).")

        return cleaned_data
