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
