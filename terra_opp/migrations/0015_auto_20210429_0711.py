# Generated by Django 3.2 on 2021-04-29 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("terra_opp", "0014_auto_20210427_1247"),
    ]

    operations = [
        migrations.AlterField(
            model_name="picture",
            name="state",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("submited", "Submitted"),
                    ("accepted", "Accepted"),
                    ("refused", "Refused"),
                ],
                default="draft",
                max_length=10,
                verbose_name="State",
            ),
        ),
        migrations.AlterField(
            model_name="viewpoint",
            name="active",
            field=models.BooleanField(default=False, verbose_name="Active"),
        ),
    ]