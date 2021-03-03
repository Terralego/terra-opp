from django.test import TestCase
from terra_opp.tests.factories import ViewpointFactory


class ViewpointModelTestCase(TestCase):
    def test_identifier_is_set_on_save_for_first_viewpoint(self):
        """
        Creating a viewpoint when base is empty should init identifier to 0
        Then, it should increment by one the viewpoint identifier each time a new one is created
        If viewpoint identifier is specified at creation, it should take this paremeter
        """
        viewpoint_1 = ViewpointFactory(label="First viewpoint")
        self.assertEqual(viewpoint_1.identifier, 1)

        viewpoint_2 = ViewpointFactory(label="Second viewpoint")
        self.assertEqual(viewpoint_2.identifier, 2)

        fix_identifier = 42
        viewpoint_3 = ViewpointFactory(
            label="Third viewpoint", identifier=fix_identifier
        )
        self.assertEqual(viewpoint_3.identifier, fix_identifier)

        viewpoint_4 = ViewpointFactory(label="Fourth viewpoint")
        self.assertEqual(viewpoint_4.identifier, fix_identifier + 1)
