# Generated by Django 2.0.13 on 2019-07-15 09:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('terra_opp', '0004_auto_20190711_1801'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='document',
            name='viewpoint',
        ),
        migrations.DeleteModel(
            name='Document',
        ),
    ]
