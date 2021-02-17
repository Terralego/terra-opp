from django.template import Context, Template
from django.test import TestCase

from terra_opp.tests.factories import ViewpointFactory


class AsVersatileTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create viewpoint with draft picture attached to it
        cls.viewpoint = ViewpointFactory(label="Basic viewpoint")

    def test_image_loader_object(self):
        self.maxDiff = None
        context = Context({"picture": self.viewpoint.pictures.all()[0]})
        template_to_render = Template(
            "{% load opp_tags %}{{ picture.file|as_versatile:'thumbnail__750x1500' }}"
        )
        rendered_template = template_to_render.render(context)
        self.assertIn("750x1500", rendered_template)
