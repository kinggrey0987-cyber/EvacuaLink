from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        TECHNICAL_ADMIN = "TECHNICAL_ADMIN", "Technical Administrator"
        ADMIN = "ADMIN", "Administrator"
        STAFF = "STAFF", "Staff"

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STAFF)
    phone_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_verified_responder = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        """Auto-sync Django admin access for technical administrators."""
        self.is_staff = self.role == self.Role.TECHNICAL_ADMIN
        self.is_superuser = self.role == self.Role.TECHNICAL_ADMIN
        super().save(*args, **kwargs)

    @property
    def is_technical_admin(self):
        """Check if user manages system accounts and technical admin tools."""
        return self.role == self.Role.TECHNICAL_ADMIN

    @property
    def is_emergency_responder(self):
        """Check if user can manage operational evacuation workflows."""
        return self.role == self.Role.STAFF

    @property
    def is_operational_admin(self):
        """Check if user can view the overall operational system."""
        return self.role == self.Role.ADMIN
