from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("emergency", "0005_help_request_location_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="emergencyhelprequest",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="help_request_photos/"),
        ),
    ]
