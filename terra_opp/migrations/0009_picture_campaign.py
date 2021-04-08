# Generated by Django 2.2.18 on 2021-04-06 15:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("terra_opp", "0008_migrate_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="picture",
            name="campaign",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pictures",
                to="terra_opp.Campaign",
            ),
        ),
    ]
