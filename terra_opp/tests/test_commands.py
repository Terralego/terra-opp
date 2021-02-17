from django.core.management import call_command
from django.test import TestCase, override_settings
from io import StringIO

from geostore import GeometryTypes
from geostore.models import Layer


class CreateDefaultObservatoryLayerTEstCase(TestCase):
    @override_settings(TROPP_OBSERVATORY_LAYER_PK=None)
    def test_create_without_existing_layer(self):
        out = StringIO()
        call_command("create_observatory_layer", name="test", stdout=out)
        self.assertIn("Layer has been created", out.getvalue())

    @override_settings(TROPP_OBSERVATORY_LAYER_PK=99999)
    def test_create_with_nonexisting_configured_layer(self):
        out = StringIO()
        call_command("create_observatory_layer", name="test", stdout=out)
        self.assertIn("does not exists in database", out.getvalue())

    @override_settings(TROPP_OBSERVATORY_LAYER_PK=99999)
    def test_force_create_with_nonexisting_configured_layer(self):
        out = StringIO()
        call_command("create_observatory_layer", name="test", force=True, stdout=out)
        self.assertIn("Layer has been created", out.getvalue())

    def test_force_create_with_existing_configured_layer(self):
        out = StringIO()
        layer = Layer.objects.create(name="tmp", geom_type=GeometryTypes.Point)
        with override_settings(TROPP_OBSERVATORY_LAYER_PK=layer.pk):
            call_command(
                "create_observatory_layer", name="test", force=True, stdout=out
            )
            self.assertIn("A layer already exists", out.getvalue())

    @override_settings(TROPP_OBSERVATORY_LAYER_PK=99999)
    def test_create_with_existing_name(self):
        out = StringIO()
        # create a layer with name test
        Layer.objects.create(name="test", geom_type=GeometryTypes.Point)
        call_command("create_observatory_layer", name="test", force=True, stdout=out)
        self.assertIn("already exists for this name", out.getvalue())

    def test_create_with_right_settings(self):
        out = StringIO()
        # create a layer
        layer = Layer.objects.create(name="tmp", geom_type=GeometryTypes.Point)
        with override_settings(TROPP_OBSERVATORY_LAYER_PK=layer.pk):
            call_command("create_observatory_layer", name="test", stdout=out)
            self.assertIn("A layer already exists", out.getvalue())
