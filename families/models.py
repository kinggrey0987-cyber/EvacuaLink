from django.db import models


class Family(models.Model):
    class ReunificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partially Reunified"
        REUNIFIED = "REUNIFIED", "Reunified"
        UNKNOWN = "UNKNOWN", "Unknown"

    family_code = models.CharField(max_length=50, unique=True)
    family_name = models.CharField(max_length=150, default="Unnamed Family")
    contact_person = models.CharField(max_length=150, default="Unknown")
    contact_number = models.CharField(max_length=30, blank=True)
    reunification_status = models.CharField(
        max_length=30, choices=ReunificationStatus.choices, default=ReunificationStatus.PENDING
    )

    class Meta:
        ordering = ["family_name"]
        verbose_name_plural = "families"

    def __str__(self):
        return f"{self.family_code} - {self.family_name}"

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

