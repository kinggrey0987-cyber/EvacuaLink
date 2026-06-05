from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("families", "0003_alter_family_options_remove_family_barangay_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="FamilyReunificationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "old_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PENDING", "Pending"),
                            ("PARTIAL", "Partially Reunified"),
                            ("REUNIFIED", "Reunified"),
                            ("UNKNOWN", "Unknown"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "new_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PARTIAL", "Partially Reunified"),
                            ("REUNIFIED", "Reunified"),
                            ("UNKNOWN", "Unknown"),
                        ],
                        max_length=30,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "family",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reunification_logs",
                        to="families.family",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
