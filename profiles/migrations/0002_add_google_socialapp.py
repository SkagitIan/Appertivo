"""Create SocialApp for Google provider used in tests."""
from django.db import migrations


def create_google_app(apps, schema_editor):
    SocialApp = apps.get_model("socialaccount", "SocialApp")
    Site = apps.get_model("sites", "Site")
    site, _ = Site.objects.get_or_create(domain="example.com", defaults={"name": "example"})
    app, _ = SocialApp.objects.get_or_create(
        provider="google", name="Google", client_id="id", secret="secret"
    )
    app.sites.add(site)


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0001_initial"),
        ("sites", "0001_initial"),
        ("socialaccount", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_google_app)]
