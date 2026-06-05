from django.db import migrations, models


def normalize_roles(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(role__in=["COORDINATOR", "VOLUNTEER"]).update(
        role="STAFF",
        is_staff=False,
        is_superuser=False,
    )
    User.objects.filter(role="ADMIN").update(is_staff=False, is_superuser=False)
    User.objects.filter(role="TECHNICAL_ADMIN").update(is_staff=True, is_superuser=True)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_user_role"),
    ]

    operations = [
        migrations.RunPython(normalize_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("TECHNICAL_ADMIN", "Technical Administrator"),
                    ("ADMIN", "Administrator"),
                    ("STAFF", "Staff"),
                ],
                default="STAFF",
                max_length=30,
            ),
        ),
    ]
