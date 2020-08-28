# Generated by Django 2.2.5 on 2020-06-30 13:15

from django.db import migrations, models
import django.db.models.deletion


def set_city_and_themes_from_properties(app, schema_editor):
    Viewpoint = app.get_model('terra_opp', 'Viewpoint')
    City = app.get_model('terra_opp', 'City')
    Theme = app.get_model('terra_opp', 'Theme')
    for viewpoint in Viewpoint.objects.all():
        city, created = City.objects.get_or_create(label=viewpoint.properties['commune'])
        viewpoint.city = city
        for theme in viewpoint.properties['themes']:
            theme, created = Theme.objects.get_or_create(label=theme)
            viewpoint.themes.add(theme)
        viewpoint.save()


class Migration(migrations.Migration):

    dependencies = [
        ('terra_opp', '0002_remove_picture_remarks'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(max_length=100, verbose_name='Label')),
            ],
            options={
                'abstract': False,
                'verbose_name_plural': 'Cities',
            },
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(max_length=100, verbose_name='Label')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='viewpoint',
            name='city',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='viewpoints', to='terra_opp.City'),
        ),
        migrations.AddField(
            model_name='viewpoint',
            name='themes',
            field=models.ManyToManyField(related_name='viewpoints', to='terra_opp.Theme'),
        ),
        migrations.RunPython(set_city_and_themes_from_properties, reverse_code=migrations.RunPython.noop),
    ]
