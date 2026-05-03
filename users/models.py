from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        TECHNICAL_ADMIN = "TECHNICAL_ADMIN", "Technical Administrator"  # System config only
        ADMIN = "ADMIN", "Operational Administrator"  # Emergency management
        COORDINATOR = "COORDINATOR", "Coordinator"
        VOLUNTEER = "VOLUNTEER", "Volunteer"
        STAFF = "STAFF", "Staff"

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STAFF)
    phone_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_verified_responder = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        """Auto-sync role with Django is_staff/is_superuser"""
        if self.role == self.Role.TECHNICAL_ADMIN:
            self.is_staff = True
            self.is_superuser = True
        else:
            # Operational roles should NOT have Django admin access
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    @property
    def is_technical_admin(self):
        """Check if user has technical admin access (Django admin)"""
        return self.role == self.Role.TECHNICAL_ADMIN

    @property
    def is_emergency_responder(self):
        """Check if user has emergency responder access (Operational)"""
        return self.role in {self.Role.ADMIN, self.Role.COORDINATOR, self.Role.VOLUNTEER}

    @property
    def is_operational_admin(self):
        """Check if user is operational admin"""
        return self.role == self.Role.ADMIN
