from django.db import migrations


def seed_brand_resources(apps, schema_editor):
    Brand = apps.get_model("core_app", "Brand")
    MonitoredResource = apps.get_model("core_app", "MonitoredResource")
    database = schema_editor.connection.alias

    for brand in Brand.objects.using(database).iterator():
        MonitoredResource.objects.using(database).get_or_create(
            brand_id=brand.pk,
            resource_type="website",
            defaults={
                "name": brand.name,
                "url": brand.official_website,
                "enabled": not brand.fl_disabled,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core_app", "0012_monitoredresource"),
    ]

    operations = [
        migrations.RunPython(seed_brand_resources, migrations.RunPython.noop),
    ]
