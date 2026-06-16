from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from evacuation_centers.models import EvacuationCenter
from families.models import Family


class Evacuee(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        CHECKED_IN = "CHECKED_IN", "Checked In"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        CHECKED_OUT = "CHECKED_OUT", "Checked Out"
        MISSING = "MISSING", "Missing"
        REUNITED = "REUNITED", "Reunited"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(130)])
    gender = models.CharField(max_length=10, choices=Gender.choices)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True, related_name="evacuees")
    evacuation_center = models.ForeignKey(
        EvacuationCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name="evacuees"
    )
    special_needs = models.BooleanField(default=False)
    special_needs_description = models.TextField(blank=True)
    medical_condition = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERED)
    registered_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.full_name} - {self.status}"

    def clean(self):
        if self.special_needs and not self.special_needs_description.strip():
            raise ValidationError(
                {"special_needs_description": "Describe the special needs when special_needs is selected."}
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-sync Family Reunification Status
        family = self.family
        if family:
            centers = family.get_evacuation_centers()
            if family.is_fully_reunified and len(centers) <= 1:
                if family.reunification_status != family.ReunificationStatus.REUNIFIED:
                    family.reunification_status = family.ReunificationStatus.REUNIFIED
                    family.save()
            else:
                if family.reunification_status == family.ReunificationStatus.REUNIFIED:
                    if family.is_partially_reunified:
                        family.reunification_status = family.ReunificationStatus.PARTIAL
                    else:
                        family.reunification_status = family.ReunificationStatus.PENDING
                    family.save()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_checked_in(self):
        return self.status == self.Status.CHECKED_IN


class TransferRecord(models.Model):
    evacuee = models.ForeignKey(Evacuee, on_delete=models.CASCADE, related_name="transfer_records")
    from_center = models.ForeignKey(
        EvacuationCenter, on_delete=models.PROTECT, related_name="outgoing_transfer_records"
    )
    to_center = models.ForeignKey(EvacuationCenter, on_delete=models.PROTECT, related_name="incoming_transfer_records")
    transfer_date = models.DateTimeField()
    reason = models.TextField()

    class Meta:
        ordering = ["-transfer_date"]

    def __str__(self):
        return f"{self.evacuee.full_name}: {self.from_center.name} to {self.to_center.name}"

    def clean(self):
        if self.from_center_id and self.to_center_id and self.from_center_id == self.to_center_id:
            raise ValidationError({"to_center": "Destination center must be different from origin center."})
