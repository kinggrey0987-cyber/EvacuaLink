"""
Forms for report generation and filtering.
"""

from django import forms
from django.utils import timezone
from datetime import timedelta

from .models import Report
from evacuation_centers.models import EvacuationCenter


class ReportFilterForm(forms.Form):
    """Form for filtering and generating reports"""

    REPORT_CHOICES = [
        ("OCCUPANCY", "Occupancy Report - Center capacity and occupancy status"),
        ("FAMILY_REUNIFICATION", "Family Reunification Report - Family status and progress"),
        ("SPECIAL_NEEDS", "Special Needs Report - Evacuees with special requirements"),
        ("INCIDENT", "Incident Report - Emergency incidents and responses"),
    ]

    report_type = forms.ChoiceField(
        label="Report Type",
        choices=REPORT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )

    date_from = forms.DateField(
        label="From Date",
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
        }),
        required=False,
        initial=timezone.now().date() - timedelta(days=30),
    )

    date_to = forms.DateField(
        label="To Date",
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
        }),
        required=False,
        initial=timezone.now().date(),
    )

    evacuation_center = forms.ModelChoiceField(
        label="Evacuation Center (Optional)",
        queryset=EvacuationCenter.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
        empty_label="All Centers",
    )

    format = forms.ChoiceField(
        label="Export Format",
        choices=[
            ("html", "View in Browser (HTML)"),
            ("pdf", "Download as PDF"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="html",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order centers by name
        self.fields["evacuation_center"].queryset = EvacuationCenter.objects.all().order_by("name")
