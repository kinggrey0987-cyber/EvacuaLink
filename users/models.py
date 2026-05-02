from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        COORDINATOR = "COORDINATOR", "Coordinator"
        VOLUNTEER = "VOLUNTEER", "Volunteer"
        STAFF = "STAFF", "Staff"

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STAFF)
    phone_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_verified_responder = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_emergency_responder(self):
        return self.role in {self.Role.ADMIN, self.Role.COORDINATOR, self.Role.VOLUNTEER}
