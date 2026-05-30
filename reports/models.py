from django.conf import settings
from django.db import models

from evacuation_centers.models import EvacuationCenter


class Report(models.Model):
    class ReportType(models.TextChoices):
        OCCUPANCY = "OCCUPANCY", "Occupancy"
        INCIDENT = "INCIDENT", "Incident"
        SUPPLIES = "SUPPLIES", "Supplies"
        EVACUEE_SUMMARY = "EVACUEE_SUMMARY", "Evacuee Summary"
        FAMILY_REUNIFICATION = "FAMILY_REUNIFICATION", "Family Reunification"
        SPECIAL_NEEDS = "SPECIAL_NEEDS", "Special Needs"

    title = models.CharField(max_length=150)
    report_type = models.CharField(max_length=30, choices=ReportType.choices)
    evacuation_center = models.ForeignKey(EvacuationCenter, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
