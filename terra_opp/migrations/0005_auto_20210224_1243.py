# Generated by Django 2.2.18 on 2021-02-24 12:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("terra_opp", "0004_viewpoint_active"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="campaign",
            options={
                "ordering": ["-created_at"],
                "permissions": (("manage_campaigns", "Can manage all campaigns"),),
            },
        ),
        migrations.AddField(
            model_name="campaign",
            name="start_date",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Start date"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="campaign",
            name="label",
            field=models.CharField(max_length=250, verbose_name="Label"),
        ),
    ]
