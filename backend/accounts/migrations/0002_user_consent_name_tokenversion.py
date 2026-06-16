"""Wave 1: add full_name, NDPR consent timestamps, and the token_version lever.

`full_name` is non-null; existing rows (the seeded Ops superuser, any deployed
accounts) get a one-off empty default. Registration enforces a real name at the
serializer layer.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="full_name",
            field=models.CharField(default="", max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="phone_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="tos_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="privacy_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="token_version",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="purged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
