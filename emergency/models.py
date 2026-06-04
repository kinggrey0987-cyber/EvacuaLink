from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from evacuation_centers.models import EvacuationCenter


class EmergencyIncident(models.Model):
    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MODERATE = "MODERATE", "Moderate"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESPONDING = "RESPONDING", "Responding"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    title = models.CharField(max_length=150)
    description = models.TextField()
    location = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MODERATE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    evacuation_center = models.ForeignKey(EvacuationCenter, on_delete=models.SET_NULL, null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-reported_at"]

    def __str__(self):
        return f"{self.title} ({self.severity})"


class EmergencyHelpRequest(models.Model):
    class LocationSource(models.TextChoices):
        AUTO_GPS = "AUTO_GPS", "Auto GPS"
        MAP_PIN = "MAP_PIN", "Map Pin"
        MANUAL = "MANUAL", "Manual Entry"
        ADMIN_CORRECTED = "ADMIN_CORRECTED", "Admin Corrected"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CANCELLED = "CANCELLED", "Cancelled"

    requester_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=30)
    location_description = models.TextField()
    message = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    location_source = models.CharField(max_length=20, choices=LocationSource.choices, default=LocationSource.MAP_PIN)
    location_accuracy = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Estimated GPS accuracy in meters")
    photo = models.ImageField(upload_to="help_request_photos/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.requester_name} - {self.status}"

    def clean(self):
        if self.status == self.Status.RESOLVED and self.resolved_at is None:
            raise ValidationError({"resolved_at": "Resolved requests must include a resolved timestamp."})
