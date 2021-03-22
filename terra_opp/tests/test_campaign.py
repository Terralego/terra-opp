from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from terra_accounts.tests.factories import TerraUserFactory
from terra_opp.tests.factories import CampaignFactory, ViewpointFactory
from terra_opp.tests.mixins import TestPermissionsMixin


class CampaignTestCase(TestPermissionsMixin, APITestCase):
    def setUp(self):
        self.photograph = TerraUserFactory()
        self.user = TerraUserFactory()

    def test_list_campaign(self):
        viewpoint2 = ViewpointFactory()
        viewpoint = ViewpointFactory()
        campaign = CampaignFactory(assignee=self.photograph, state="started")
        campaign.viewpoints.set([viewpoint, viewpoint2])

        campaign_other = CampaignFactory(
            state="started"
        )  # campaign for other photograph

        list_url = reverse("terra_opp:campaign-list")
        campaign_url = resolve_url("terra_opp:campaign-detail", pk=campaign.pk)
        campaign_other_url = resolve_url(
            "terra_opp:campaign-detail", pk=campaign_other.pk
        )

        # First we try as anonymous
        self.assertIn(
            self.client.get(list_url).status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        self.assertIn(
            self.client.get(campaign_url).status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        self.assertIn(
            self.client.get(campaign_other_url).status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

        # Then with add_picture rights
        self.client.force_authenticate(user=self.photograph)
        self._set_permissions(
            [
                "can_add_pictures",
            ],
            self.photograph,
        )
        response = self.client.get(list_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, response.data.get("count"))
        # Temp commented
        """self.assertIn(
            viewpoint.pictures.first().file.url,
            response.data.get("results")[0].get("picture").get("original"),
        )"""

        response = self.client.get(campaign_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # Temp commented
        """self.assertIn(
            viewpoint.pictures.first().file.url,
            response.data.get("viewpoints")[0].get("picture").get("original"),
        )"""
        self.assertEqual(
            status.HTTP_403_FORBIDDEN, self.client.get(campaign_other_url).status_code
        )

        # Then as admin
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_campaigns",
            ],
        )
        response = self.client.get(list_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, response.data.get("count"))

        self.assertEqual(status.HTTP_200_OK, self.client.get(campaign_url).status_code)
        self.assertEqual(
            status.HTTP_200_OK, self.client.get(campaign_other_url).status_code
        )

    @override_settings(TROPP_PICTURES_STATES_WORKFLOW=True)
    def test_get_campaign(self):
        campaign = CampaignFactory(assignee=self.photograph)
        campaign_url = resolve_url("terra_opp:campaign-detail", pk=campaign.pk)
        self.client.force_authenticate(user=self.photograph)

        viewpoint = ViewpointFactory()
        viewpoint.pictures.all().delete()
        campaign.viewpoints.set([viewpoint])
        self.client.get(campaign_url)

        viewpoint = ViewpointFactory()
        campaign.viewpoints.set([viewpoint])
        self.client.get(campaign_url)

        # TODO add assertion

    @override_settings(TROPP_PICTURES_STATES_WORKFLOW=True)
    def test_search_campaign(self):
        campaign = CampaignFactory(assignee=self.photograph)
        # list_url = resolve_url("terra_opp:campaign-list")
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_campaigns",
            ]
        )

        viewpoint = ViewpointFactory()
        campaign.viewpoints.set([viewpoint])
        # Picture state is draft
        # Commented for now
        """response = self.client.get(list_url, {"state": "draft"})
        self.assertEqual(1, response.data.get("count"))
        response = self.client.get(list_url, {"state": "started"})
        self.assertEqual(0, response.data.get("count"))
        response = self.client.get(list_url, {"picture_status": "draft"})
        self.assertEqual(1, response.data.get("count"))
        response = self.client.get(list_url, {"picture_status": "accepted"})
        self.assertEqual(0, response.data.get("count"))

        viewpoint.pictures.update(state="accepted")
        response = self.client.get(list_url, {"state": "draft"})
        self.assertEqual(0, response.data.get("count"))
        response = self.client.get(list_url, {"state": "started"})
        self.assertEqual(1, response.data.get("count"))
        response = self.client.get(list_url, {"picture_status": "draft"})
        self.assertEqual(0, response.data.get("count"))
        response = self.client.get(list_url, {"picture_status": "accepted"})
        self.assertEqual(1, response.data.get("count"))"""

    def test_post_campaign(self):
        data = {
            "label": "My campaign",
            "start_date": "2021-01-25",
            "assignee": self.photograph.pk,
            "viewpoints": [ViewpointFactory().pk, ViewpointFactory().pk],
        }

        self.client.force_authenticate(user=self.photograph)
        response = self.client.post(reverse("terra_opp:campaign-list"), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_campaigns",
            ]
        )
        response = self.client.post(reverse("terra_opp:campaign-list"), data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
