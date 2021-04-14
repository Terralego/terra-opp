from django.test import TestCase
from terra_opp.models import City


class CitiesTestCase(TestCase):
    def setUp(self):
        City.objects.create(label="LYON")
        City.objects.create(label="pARIS")

    def test_capitalize(self):
        self.assertTrue(City.objects.filter(label="Lyon").exists())
        self.assertFalse(City.objects.filter(label="LYON").exists())

        self.assertTrue(City.objects.filter(label="Paris").exists())
        self.assertFalse(City.objects.filter(label="pARIS").exists())
