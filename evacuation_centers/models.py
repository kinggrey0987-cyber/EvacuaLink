from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class EvacuationCenter(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        FULL = "FULL", "Full"
        CLOSED = "CLOSED", "Closed"
        UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Under Maintenance"

    name = models.CharField(max_length=150, unique=True)
    address = models.TextField()
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, default=0, validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, default=0, validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    current_occupancy = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    # OOP_PRESENTATION: POLYMORPHISM (Method Overriding - different output for centers)
    def __str__(self):
        return f"{self.name} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-update OPEN/FULL status based on real occupancy
        # We don't override CLOSED or UNDER_MAINTENANCE manually set by staff
        if self.status not in [self.Status.CLOSED, self.Status.UNDER_MAINTENANCE]:
            if self.current_occupancy >= self.capacity:
                self.status = self.Status.FULL
            else:
                self.status = self.Status.OPEN
        super().save(*args, **kwargs)

    def available_space(self):
        return max(self.capacity - self.current_occupancy, 0)

    def is_full(self):
        return self.current_occupancy >= self.capacity or self.status == self.Status.FULL

    @property
    def occupancy_rate(self):
        return round((self.current_occupancy / self.capacity) * 100, 2)

    @property
    def available_slots(self):
        return self.available_space()
