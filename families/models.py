from django.db import models
from django.conf import settings


class Family(models.Model):
    class ReunificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partially Reunified"
        REUNIFIED = "REUNIFIED", "Reunified"
        UNKNOWN = "UNKNOWN", "Unknown"

    family_code = models.CharField(max_length=50, unique=True, blank=True)
    family_name = models.CharField(max_length=150, default="Unnamed Family")
    contact_person = models.ForeignKey(
        'evacuees.Evacuee', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="primary_contact_for"
    )
    contact_number = models.CharField(max_length=30, blank=True)
    reunification_status = models.CharField(
        max_length=30, choices=ReunificationStatus.choices, default=ReunificationStatus.PENDING
    )

    class Meta:
        ordering = ["family_name"]
        verbose_name_plural = "families"

    def __str__(self):
        return f"{self.family_code} - {self.family_name}"

    def save(self, *args, **kwargs):
        if not self.family_code:
            import datetime
            year = datetime.datetime.now().year
            prefix = f"FAM-{year}-"
            last_family = Family.objects.filter(family_code__startswith=prefix).order_by('id').last()
            if last_family:
                try:
                    last_num = int(last_family.family_code.split('-')[-1])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            self.family_code = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        """Get total number of family members"""
        if hasattr(self, "num_members"):
            return self.num_members
        return self.evacuees.count()

    @property
    def checked_in_count(self):
        """Get number of members checked in"""
        if hasattr(self, "num_checked_in"):
            return self.num_checked_in
        return self.evacuees.filter(status="CHECKED_IN").count()

    @property
    def reunited_count(self):
        """Get number of members reunited"""
        if hasattr(self, "num_reunited"):
            return self.num_reunited
        return self.evacuees.filter(status="REUNITED").count()

    @property
    def missing_count(self):
        """Get number of missing members"""
        if hasattr(self, "num_missing"):
            return self.num_missing
        return self.evacuees.filter(status="MISSING").count()

    @property
    def is_fully_reunified(self):
        """Check if all family members are reunited"""
        if self.member_count == 0:
            return False
        return self.reunited_count == self.member_count

    @property
    def is_partially_reunified(self):
        """Check if some family members are reunited"""
        return self.reunited_count > 0 and self.reunited_count < self.member_count

    def get_evacuation_centers(self):
        """Get all evacuation centers where family members are located"""
        from evacuees.models import Evacuee
        centers = set()
        for evacuee in self.evacuees.all():
            if evacuee.evacuation_center:
                centers.add(evacuee.evacuation_center)
        return list(centers)

    def get_family_members_list(self):
        """Get all family members with their details"""
        return self.evacuees.select_related("evacuation_center").order_by("last_name", "first_name")


class FamilyReunificationLog(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="reunification_logs")
    old_status = models.CharField(max_length=30, choices=Family.ReunificationStatus.choices, blank=True)
    new_status = models.CharField(max_length=30, choices=Family.ReunificationStatus.choices)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.family.family_code}: {self.old_status or 'NEW'} to {self.new_status}"
