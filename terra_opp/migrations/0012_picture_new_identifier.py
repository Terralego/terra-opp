# Generated by Django 3.2 on 2021-04-13 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("terra_opp", "0011_auto_20210412_1000"),
    ]

    operations = [
        migrations.AddField(
            model_name="picture",
            name="new_identifier",
            field=models.CharField(
                default="", max_length=10, verbose_name="Identifier"
            ),
        ),
    ]
