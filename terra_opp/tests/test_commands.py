from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from io import StringIO

from geostore import GeometryTypes
from geostore.models import Layer


class CreateDefaultObservatoryLayerTEstCase(TestCase):
    @override_settings(TROPP_OBSERVATORY_LAYER_PK=None)
    def test_create_without_existing_layer(self):
        out = StringIO()
        call_command('create_observatory_layer', name="test", stdout=out)
        self.assertIn("Layer has been created", out.getvalue())

    @override_settings(TROPP_OBSERVATORY_LAYER_PK=99999)
    def test_create_with_wrong_settings(self):
        with self.assertRaises(CommandError):
            call_command('create_observatory_layer', name="test")

    def test_create_with_right_settings(self):
        out = StringIO()
        # create a layer
        layer = Layer.objects.create(name='tmp', geom_type=GeometryTypes.Point)
        with override_settings(TROPP_OBSERVATORY_LAYER_PK=layer.pk):
            call_command('create_observatory_layer', name="test", stdout=out)
            self.assertIn("An existing layer already exists", out.getvalue())
