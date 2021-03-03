# Generated by Django 3.1.7 on 2021-02-24 07:50

from django.db import migrations


def populate_viewpoint_identifier(apps, schema_editor):
    ViewpointModel = apps.get_model("terra_opp", "Viewpoint")
    for viewpoint in ViewpointModel.objects.all():
        viewpoint.identifier = viewpoint.properties.pop("index")
        viewpoint.save()


def revert_populate_viewpoint_identifier(apps, schema_editor):
    ViewpointModel = apps.get_model("terra_opp", "Viewpoint")
    for viewpoint in ViewpointModel.objects.all():
        viewpoint.properties["index"] = viewpoint.identifier
        viewpoint.save()


class Migration(migrations.Migration):

    dependencies = [
        ("terra_opp", "0004_viewpoint_identifier"),
    ]

    operations = [
        migrations.RunPython(
            populate_viewpoint_identifier, revert_populate_viewpoint_identifier
        )
    ]
