from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from terra_accounts.tests.factories import TerraUserFactory
from terra_opp.tests.factories import CampaignFactory, ViewpointFactory, PictureFactory
from terra_opp.tests.mixins import TestPermissionsMixin


class CampaignTestCase(TestPermissionsMixin, APITestCase):
    def setUp(self):
        self.photograph = TerraUserFactory()
        self.user = TerraUserFactory()

    def _gen_file(self):
        return SimpleUploadedFile(
            name="add_picture_test.jpg",
            content=open(
                "terra_opp/tests/placeholder.jpg",
                "rb",
            ).read(),
            content_type="image/jpeg",
        )

    def _authent(self, user, permissions):
        self.client.force_authenticate(user=user)
        self._set_permissions(
            permissions,
            user,
        )

    def as_photograph(self):
        self._authent(self.photograph, ["can_add_pictures"])

    def as_admin(self):
        self._authent(self.user, ["can_manage_campaigns", "can_manage_pictures"])

    def test_list_campaign(self):
        viewpoint = ViewpointFactory()
        viewpoint2 = ViewpointFactory()
        campaign = CampaignFactory(assignee=self.photograph, state="started")
        campaign.viewpoints.set([viewpoint, viewpoint2])

        campaign_other = CampaignFactory(
            state="started"
        )  # campaign for other photograph

        campaign_same_not_started = CampaignFactory(
            state="draft", assignee=self.photograph
        )  # campaign for same photograph but not started

        list_url = reverse("terra_opp:campaign-list")
        campaign_url = resolve_url("terra_opp:campaign-detail", pk=campaign.pk)
        campaign_other_url = resolve_url(
            "terra_opp:campaign-detail", pk=campaign_other.pk
        )
        campaign_not_started_url = resolve_url(
            "terra_opp:campaign-detail", pk=campaign_same_not_started.pk
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

        # Then we try with can_add_pictures permission
        self.as_photograph()

        response = self.client.get(list_url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # Only one should be visible
        self.assertEqual(1, response.data.get("count"))

        response = self.client.get(campaign_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # Others campaigns should be forbidden
        self.assertEqual(
            status.HTTP_403_FORBIDDEN, self.client.get(campaign_other_url).status_code
        )
        # Not started campaigns should forbidden
        self.assertEqual(
            status.HTTP_403_FORBIDDEN,
            self.client.get(campaign_not_started_url).status_code,
        )

        # Then as admin
        self.as_admin()

        response = self.client.get(list_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.data.get("count"), 3)

        self.assertEqual(status.HTTP_200_OK, self.client.get(campaign_url).status_code)
        self.assertEqual(
            status.HTTP_200_OK, self.client.get(campaign_other_url).status_code
        )
        self.assertEqual(
            status.HTTP_200_OK, self.client.get(campaign_not_started_url).status_code
        )

    def test_search_campaign(self):
        viewpoint = ViewpointFactory(pictures__state="accepted")

        campaign = CampaignFactory(assignee=self.photograph)
        campaign.viewpoints.set([viewpoint])

        campaign2 = CampaignFactory(assignee=self.photograph, state="started")
        campaign3 = CampaignFactory(assignee=self.photograph, state="closed")

        picture = PictureFactory(state="draft", viewpoint=viewpoint, campaign=campaign)

        list_url = resolve_url("terra_opp:campaign-list")

        self.as_admin()

        response = self.client.get(list_url, {"state": "draft"})
        self.assertEqual(1, response.data.get("count"))

        response = self.client.get(list_url, {"state": "started"})
        self.assertEqual(1, response.data.get("count"))

        response = self.client.get(list_url, {"state": "closed"})
        self.assertEqual(1, response.data.get("count"))

        response = self.client.get(list_url, {"state": "foo"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(list_url, {"pictures__state": "draft"})
        self.assertEqual(1, response.data.get("count"))
        response = self.client.get(list_url, {"pictures__state": "accepted"})
        self.assertEqual(0, response.data.get("count"))

        picture.state = "accepted"
        picture.save()

        response = self.client.get(list_url, {"pictures__state": "draft"})
        self.assertEqual(0, response.data.get("count"))
        response = self.client.get(list_url, {"pictures__state": "accepted"})
        self.assertEqual(1, response.data.get("count"))

        response = self.client.get(list_url, {"pictures__state": "foo"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_campaign(self):
        data = {
            "label": "My campaign",
            "start_date": "2021-01-25",
            "assignee": self.photograph.pk,
            "viewpoints": [ViewpointFactory().pk, ViewpointFactory().pk],
        }

        self.as_photograph()

        response = self.client.post(reverse("terra_opp:campaign-list"), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.as_admin()

        response = self.client.post(reverse("terra_opp:campaign-list"), data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_add_picture(self):
        viewpoint = ViewpointFactory()
        viewpoint2 = ViewpointFactory()
        viewpoint3 = ViewpointFactory()
        viewpoint4 = ViewpointFactory()
        viewpoint5 = ViewpointFactory()
        viewpoint6 = ViewpointFactory()

        campaign1 = CampaignFactory(assignee=self.photograph, state="started")
        campaign1.viewpoints.set([viewpoint, viewpoint2])
        initial_picture_count1 = viewpoint.pictures.count()

        campaign2 = CampaignFactory(assignee=self.photograph, state="draft")
        campaign2.viewpoints.set([viewpoint3, viewpoint4])

        campaign3 = CampaignFactory(state="started")
        campaign3.viewpoints.set([viewpoint5, viewpoint6])

        data = {
            "viewpoint": viewpoint.pk,
            "date": timezone.datetime(2020, 8, 19, tzinfo=timezone.utc),
            "file": self._gen_file(),
            "state": "draft",
        }

        self.as_photograph()

        # Nominal cases should works
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(viewpoint.pictures.count(), initial_picture_count1 + 1)
        self.assertEqual(
            viewpoint.pictures.latest().date,
            timezone.datetime(2020, 8, 19, tzinfo=timezone.utc),
        )
        self.assertEqual(
            viewpoint.pictures.latest().state,
            "draft",
        )

        # Should not allow to create second photo
        data["file"] = self._gen_file()
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Should update picture but ignore accepted state
        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[viewpoint.pictures.latest().pk],
            ),
            {"state": "accepted"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("state"), "draft")

        # Should update previous picture and change state
        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[viewpoint.pictures.latest().pk],
            ),
            {"state": "submited"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should not allow modification on submitted picture
        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[viewpoint.pictures.latest().pk],
            ),
            {"state": "accepted"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Post to draft campaign
        data["viewpoint"] = viewpoint3.pk
        data["file"] = self._gen_file()
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Post to started campaign for another assignee
        data["viewpoint"] = viewpoint5.pk
        data["file"] = self._gen_file()
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Post to started campaign but with bad viewpoint
        data["viewpoint"] = viewpoint5.pk
        data["file"] = self._gen_file()
        data["campaign"] = campaign1.pk
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Post to started campaign bad picture state
        data["viewpoint"] = viewpoint5.pk
        data["file"] = self._gen_file()
        data["campaign"] = campaign1.pk
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_workflow(self):
        viewpoint = ViewpointFactory()
        viewpoint2 = ViewpointFactory()

        campaign1 = CampaignFactory(assignee=self.photograph, state="started")
        campaign1.viewpoints.set([viewpoint, viewpoint2])

        data = {
            "viewpoint": viewpoint.pk,
            "date": timezone.datetime(2020, 8, 19, tzinfo=timezone.utc),
            "file": self._gen_file(),
            "state": "draft",
        }

        self.as_photograph()

        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        latest_picture = viewpoint.pictures.latest()

        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[latest_picture.pk],
            ),
            {"state": "submited"},
        )

        self.as_admin()

        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[latest_picture.pk],
            ),
            {"state": "refused"},
        )

        self.as_photograph()

        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[latest_picture.pk],
            ),
            {"state": "submited", "file": self._gen_file()},
            format="multipart",
        )

        self.as_admin()

        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[latest_picture.pk],
            ),
            {"state": "accepted"},
        )

        latest_picture.refresh_from_db()

        self.assertEqual(latest_picture.state, "accepted")

    def test_statistics(self):
        viewpoint = ViewpointFactory(pictures__state="accepted")
        viewpoint2 = ViewpointFactory(pictures__state="accepted")
        viewpoint3 = ViewpointFactory(pictures__state="accepted")
        viewpoint4 = ViewpointFactory(pictures__state="accepted")

        campaign = CampaignFactory(assignee=self.photograph, state="started")
        campaign.viewpoints.set([viewpoint, viewpoint2, viewpoint3, viewpoint4])
        campaign_url = resolve_url("terra_opp:campaign-detail", pk=campaign.pk)

        data = {
            "viewpoint": viewpoint.pk,
            "date": timezone.datetime(2020, 8, 19, tzinfo=timezone.utc),
            "file": self._gen_file(),
            "state": "draft",
        }

        # Stats without any photo
        self.as_admin()

        response = self.client.get(campaign_url)

        def stats(response):
            return response.json().get("statistics")
            """return dict(
                total=data["viewpoints_total"],
                submited=data["pictures_submited"],
                accepted=data["pictures_accepted"],
                missing=data["pictures_missing"],
            )"""

        self.assertEqual(
            stats(response),
            {"total": 4, "missing": 4, "submited": 0, "accepted": 0},
        )

        # Add draft photo
        self.as_photograph()
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        # Draft photo are considered as missing
        self.as_admin()
        response = self.client.get(campaign_url)
        self.assertEqual(
            stats(response),
            {"total": 4, "missing": 4, "submited": 0, "accepted": 0},
        )

        # Submit photo
        self.as_photograph()
        latest_picture = viewpoint.pictures.latest()
        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[latest_picture.pk],
            ),
            {"state": "submited"},
        )

        print([p.state for p in campaign.pictures.all()])

        # Should have 1 submited
        self.as_admin()
        response = self.client.get(campaign_url)
        print(response.json())
        self.assertEqual(
            stats(response),
            {"total": 4, "missing": 3, "submited": 1, "accepted": 0},
        )

        # Submit another photo
        self.as_photograph()
        data["viewpoint"] = viewpoint2.pk
        data["file"] = self._gen_file()
        data["state"] = "submited"
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )

        # Should have 2 submited
        self.as_admin()
        response = self.client.get(campaign_url)
        self.assertEqual(
            stats(response),
            {"total": 4, "missing": 2, "submited": 2, "accepted": 0},
        )

        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[latest_picture.pk],
            ),
            {"state": "accepted"},
        )

        response = self.client.get(campaign_url)
        self.assertEqual(
            stats(response),
            {"total": 4, "missing": 2, "submited": 1, "accepted": 1},
        )

        latest_picture2 = viewpoint2.pictures.latest()

        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[latest_picture2.pk],
            ),
            {"state": "refused"},
        )

        response = self.client.get(campaign_url)
        self.assertEqual(
            stats(response),
            {"total": 4, "missing": 3, "submited": 0, "accepted": 1},
        )