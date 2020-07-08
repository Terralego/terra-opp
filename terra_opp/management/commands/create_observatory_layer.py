from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _
from geostore import GeometryTypes
from geostore.models import Layer


class Command(BaseCommand):
    help = _('Create a django-geostore point layer to store observatory viewpoints')

    def add_arguments(self, parser):
        parser.add_argument('-n',
                            '--name',
                            action="store",
                            help="Name for layer to create.")

    def get_existing_layer(self):
        existing_observatory = getattr(settings, 'TROPP_OBSERVATORY_LAYER_PK')
        if existing_observatory:
            try:
                Layer.objects.get(pk=existing_observatory)
            except Layer.DoesNotExist:
                raise CommandError('Defined layer with PK "%s" defined in setting TROPP_OBSERVATORY_LAYER_PK does not exists in database' % existing_observatory)
        return existing_observatory

    def handle(self, *args, **options):
        existing_observatory = self.get_existing_layer()
        name = options.get('name')
        if existing_observatory:
            self.stdout.write(
                self.style.WARNING(
                    f"{_('An existing layer already exists for this:')} - TROPP_OBSERVATORY_LAYER_PK: {existing_observatory}"
                )
            )
        else:
            layer = Layer.objects.create(
                geom_type=GeometryTypes.Point,
                name=f"{name}"
            )
            self.stdout.write(self.style.SUCCESS(
                _('Layer has been created. Please set TROPP_OBSERVATORY_LAYER_PK=%s in project settings' % layer.pk)
            ))
