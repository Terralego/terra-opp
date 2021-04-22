import base64
import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone, dateparse
from rest_framework import status
from rest_framework.test import APITestCase

from terra_accounts.tests.factories import TerraUserFactory
from geostore.models import Feature
from geostore.tests.factories import FeatureFactory
from terra_opp.models import Picture, Viewpoint, City
from terra_opp.tests.factories import (
    CityFactory,
    PictureFactory,
    ThemeFactory,
    ViewpointFactory,
)
from terra_opp.tests.mixins import TestPermissionsMixin


@override_settings(TROPP_OBSERVATORY_ID=20)
class ViewpointCapitaliseTestCase(APITestCase, TestPermissionsMixin):
    @classmethod
    def setUpTestData(cls):
        cls.feature = FeatureFactory()
        cls.user = TerraUserFactory()

    def test_create_viewpoint(self):
        self.data_create = {
            "label": "Basic viewpoint created",
            "point": self.feature.geom.json,
            "city": "Marseille",
        }
        self.client.force_authenticate(user=self.user)
        self._set_permissions(["can_manage_viewpoints"])

        response = self.client.post(
            reverse("terra_opp:viewpoint-list"),
            self.data_create,
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())
        self.assertEqual(response.json()["city"], "Marseille")
        self.assertTrue(City.objects.filter(label="Marseille").exists())

    def test_create_uncapitalized(self):
        self.data_create = {
            "label": "Basic viewpoint created",
            "point": self.feature.geom.json,
            "city": "marseille",
        }
        self.client.force_authenticate(user=self.user)
        self._set_permissions(["can_manage_viewpoints"])

        response = self.client.post(
            reverse("terra_opp:viewpoint-list"),
            self.data_create,
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())
        self.assertEqual(response.json()["city"], "Marseille")
        self.assertTrue(City.objects.filter(label="Marseille").exists())
        self.assertFalse(City.objects.filter(label="marseille").exists())

    def test_already_in_db(self):
        City.objects.create(label="Marseille")
        self.data_create = {
            "label": "Basic viewpoint created",
            "point": self.feature.geom.json,
            "city": "marseille",
        }
        self.client.force_authenticate(user=self.user)
        self._set_permissions(["can_manage_viewpoints"])

        response = self.client.post(
            reverse("terra_opp:viewpoint-list"),
            self.data_create,
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())
        self.assertEqual(response.json()["city"], "Marseille")
        self.assertTrue(City.objects.filter(label="Marseille").exists())
        self.assertFalse(City.objects.filter(label="marseille").exists())


@override_settings(TROPP_OBSERVATORY_ID=20)
class ViewpointTestCase(APITestCase, TestPermissionsMixin):
    @classmethod
    @override_settings(TROPP_PICTURES_STATES_WORKFLOW=True)
    def setUpTestData(cls):
        cls.feature = FeatureFactory()
        cls.user = TerraUserFactory()
        # Create viewpoint with draft picture attached to it
        cls.viewpoint = ViewpointFactory(label="Basic viewpoint")
        # Create viewpoint with accepted picture attached to it
        cls.viewpoint_with_accepted_picture = ViewpointFactory(
            label="Viewpoint with accepted picture",
            pictures__state="accepted",
            properties={"test_update": "ko"},
        )
        # Create viewpoints with no picture attached to it
        cls.viewpoint_without_picture = ViewpointFactory(
            label="Viewpoint without picture",
            pictures=None,
            properties={"test_update": "ko"},
        )

    def setUp(self):
        self.fp = open(
            os.path.join(os.path.dirname(__file__), "placeholder.jpg"),
            "rb",
        )

        self.data_create = {
            "label": "Basic viewpoint created",
            "point": self.feature.geom.json,
            "city": "Nantes",
        }

        self.data_create_with_picture = {
            "label": "Viewpoint created with picture",
            "point": self.feature.geom.json,
            "picture_ids": [
                picture.pk
                for picture in self.viewpoint_with_accepted_picture.pictures.all()
            ],
            "city": "Nantes",
        }

        self.data_create_with_themes = {
            "label": "Viewpoint created with themes",
            "point": self.feature.geom.json,
            "city": "Nantes",
            "themes": ["foo", "bar"],
        }
        self._clean_permissions()  # Don't forget that !

    def tearDown(self):
        self.fp.close()

    def _viewpoint_create(self):
        return self.client.post(
            reverse("terra_opp:viewpoint-list"),
            self.data_create,
        )

    def _viewpoint_create_with_picture(self):
        return self.client.post(
            reverse("terra_opp:viewpoint-list"),
            self.data_create_with_picture,
            format="multipart",
        )

    def test_viewpoint_get_list_anonymous(self):
        with self.assertNumQueries(6):
            data = self.client.get(reverse("terra_opp:viewpoint-list")).json()
        # List must contain all viewpoints WITHOUT those with no pictures
        # Pictures must also be ACCEPTED
        self.assertEqual(1, data.get("count"))

    def test_viewpoint_get_list_with_auth(self):
        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        data = self.client.get(reverse("terra_opp:viewpoint-list")).json()
        # List must still contain ALL viewpoints even those with no
        # pictures and pictures with other states than ACCEPTED
        self.assertEqual(3, data.get("count"))

    def test_anonymous_access_without_accepted_picture(self):
        # User is not authenticated yet
        response = self.client.get(
            reverse(
                "terra_opp:viewpoint-detail",
                args=[self.viewpoint_without_picture.pk],
            )
        )
        # There is no picture on the viewpoint
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_viewpoint_get_with_auth(self):
        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                "terra_opp:viewpoint-detail",
                args=[self.viewpoint_without_picture.pk],
            )
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(None, response.json()["last_accepted_picture_date"])

    def test_anonymous_options_request_returns_correct_search_filters(self):
        city1 = CityFactory(label="Montcuq")
        city2 = CityFactory(label="Rouperou-le-coquet")
        theme1 = ThemeFactory(label="Bar")
        theme2 = ThemeFactory(label="foo")
        ViewpointFactory(
            city=city1,
            themes=[theme1, theme2],
        )
        ViewpointFactory(
            city=city2,
            themes=[theme1],
        )
        data = self.client.get(reverse("terra_opp:viewpoint-filters")).json()
        self.assertEqual(data.get("cities"), ["Montcuq", "Rouperou-le-coquet"])
        self.assertEqual(data.get("themes"), ["Bar", "foo"])

    def test_authenticated_options_request_returns_all_search_filters(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(reverse("terra_opp:viewpoint-filters")).json()
        self.assertIsNotNone(data.get("cities"))
        self.assertIsNotNone(data.get("themes"))

        # Even if we have 3 users, we only get those who have pictures
        self.assertEqual(3, get_user_model().objects.count())
        self.assertEqual(2, len(data.get("photographers")))

    def test_viewpoint_search_anonymous(self):
        # Simple viewpoint search feature
        data = self.client.get(
            reverse("terra_opp:viewpoint-list"),
            {"search": "accepted"},
        ).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_search_with_auth(self):
        # Simple viewpoint search feature with auth
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse("terra_opp:viewpoint-list"),
            {"search": "Basic"},
        ).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_picture_filter_anonymous(self):
        data = self.client.get(
            reverse("terra_opp:viewpoint-list"),
            {
                "pictures__identifier": self.viewpoint_with_accepted_picture.pictures.first().identifier
            },
        ).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_picture_filter_with_auth(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse("terra_opp:viewpoint-list"),
            {
                "pictures__identifier": self.viewpoint_with_accepted_picture.pictures.first().identifier
            },
        ).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_photographer_filter_anonymous(self):
        picture = self.viewpoint_with_accepted_picture.pictures.first()
        data = self.client.get(
            reverse("terra_opp:viewpoint-list"),
            {"pictures__owner__uuid": picture.owner.uuid},
        ).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_photographer_filter_with_auth(self):
        self.client.force_authenticate(user=self.user)
        picture = self.viewpoint_with_accepted_picture.pictures.first()
        data = self.client.get(
            reverse("terra_opp:viewpoint-list"),
            {"pictures__owner__uuid": picture.owner.uuid},
        ).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_search_date(self):
        list_url = reverse("terra_opp:viewpoint-list")
        picture = self.viewpoint_with_accepted_picture.pictures.first()
        data = self.client.get(
            list_url, {"date_from": (picture.date - timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get("count"), 1)
        data = self.client.get(
            list_url, {"date_from": (picture.date + timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get("count"), 0)
        data = self.client.get(
            list_url, {"date_to": (picture.date + timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get("count"), 1)
        data = self.client.get(
            list_url, {"date_to": (picture.date - timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get("count"), 0)
        data = self.client.get(
            list_url,
            {
                "date_from": (picture.date - timedelta(days=1)).date(),
                "date_to": (picture.date + timedelta(days=1)).date(),
            },
        ).json()
        self.assertEqual(data.get("count"), 1)

        # Errors
        response = self.client.get(list_url, {"date_to": "haha"})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_viewpoint_search_json(self):
        list_url = reverse("terra_opp:viewpoint-list")
        ViewpointFactory(
            label="Viewpoint for search",
            pictures__state="accepted",
            properties={
                "voie": "coin d'en bas de la rue du bout",
                "site": "Carrière des petits violoncelles",
            },
        )
        self.assertEqual(self.client.get(list_url).json()["count"], 2)
        data = self.client.get(list_url, {"properties__voie": "rue"}).json()
        self.assertEqual(data.get("count"), 1)
        data = self.client.get(list_url, {"properties__site": "carrière"}).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_search_city(self):
        list_url = reverse("terra_opp:viewpoint-list")
        city = CityFactory(label="Rouperou-le-coquet")
        city2 = CityFactory(label="New york")
        city3 = CityFactory(label="Los angeles")
        ViewpointFactory(
            label="Viewpoint for search",
            pictures__state="accepted",
            city=city,
        )
        ViewpointFactory(
            label="Not found",
            pictures__state="accepted",
            city=city2,
        )
        ViewpointFactory(
            label="Not found also",
            pictures__state="accepted",
            city=city3,
        )
        self.assertEqual(self.client.get(list_url).json()["count"], 4)
        data = self.client.get(list_url, {"city_id": city.id}).json()
        self.assertEqual(data.get("count"), 1)
        data = self.client.get(list_url, {"city": "Rouperou-le-coquet"}).json()
        self.assertEqual(data.get("count"), 1)

    def test_viewpoint_search_themes(self):
        list_url = reverse("terra_opp:viewpoint-list")
        theme_foo = ThemeFactory(label="foo")
        theme_bar = ThemeFactory(label="bar")
        theme_baz = ThemeFactory(label="baz")
        theme_not = ThemeFactory(label="not")
        vp = ViewpointFactory(
            label="Viewpoint for search",
            pictures__state="accepted",
            properties={
                "voie": "coin d'en bas de la rue du bout",
                "site": "Carrière des petits violoncelles",
            },
        )
        vp.themes.add(theme_foo, theme_bar, theme_baz)
        self.assertEqual(self.client.get(list_url).json()["count"], 2)
        data = self.client.get(list_url, {"themes_id": [theme_foo.id]}).json()
        self.assertEqual(data.get("count"), 1)
        data = self.client.get(list_url, {"themes": ["foo"]}).json()
        self.assertEqual(data.get("count"), 1)
        data = self.client.get(
            list_url, {"themes_id": [theme_bar.id, theme_foo.id]}
        ).json()
        self.assertEqual(data.get("count"), 1)
        data = self.client.get(
            list_url, {"themes_id": [theme_bar.id, theme_not.id]}
        ).json()
        self.assertEqual(data.get("count"), 0)

    def test_viewpoint_create_anonymous(self):
        response = self._viewpoint_create()
        # User is not authenticated
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_viewpoint_create_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_create()
        # User doesn't have permission
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_create_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )
        response = self._viewpoint_create()
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())

    def test_viewpoint_create_with_picture_anonymous(self):
        response = self._viewpoint_create_with_picture()
        # User is not authenticated
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_viewpoint_create_with_picture_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_create_with_picture()
        # User doesn't have permission
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_create_with_picture_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )
        response = self._viewpoint_create_with_picture()

        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())
        viewpoint = Viewpoint.objects.get(label="Viewpoint created with picture")
        self.assertIn(
            "/2018-01-01_00-00-00",
            viewpoint.point.properties["viewpoint_picture"],
        )

    def test_viewpoint_create_with_themes_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )
        response = self.client.post(
            reverse("terra_opp:viewpoint-list"),
            self.data_create_with_themes,
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertListEqual(
            list(
                Viewpoint.objects.get(label="Viewpoint created with themes")
                .themes.all()
                .values_list("label", flat=True)
            ),
            ["foo", "bar"],
        )

    @patch("datastore.fields.FileBase64Field.to_internal_value")
    def test_viewpoint_create_with_related_docs(self, field):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )
        self.fp.seek(0)
        document = (
            f"data:image/jpg;base64,"
            f'{(base64.b64encode(self.fp.read())).decode("utf-8")}'
        )
        field.return_value = UploadedFile(
            self.fp,
            content_type="image/jpeg",
        )
        response = self.client.post(
            reverse("terra_opp:viewpoint-list"),
            {
                "label": "Viewpoint created with picture",
                "point": self.feature.geom.json,
                "related": [
                    {
                        "key": "croquis",
                        "document": document,
                    }
                ],
                "city": "Nantes",
            },
            format="json",
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        data = response.json()
        self.assertEqual(1, len(data["related"]))
        self.assertEqual("croquis", data["related"][0]["key"])

        # Update it
        response = self.client.patch(
            reverse("terra_opp:viewpoint-detail", args=[data["id"]]),
            {
                "related": [
                    {
                        "key": "emplacement",
                        "document": document,
                    }
                ]
            },
            format="json",
        )
        # Request is correctly constructed and viewpoint has been updated
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.json()
        self.assertEqual(1, len(data["related"]))
        self.assertEqual("emplacement", data["related"][0]["key"])

    def _viewpoint_delete(self):
        return self.client.delete(
            reverse("terra_opp:viewpoint-detail", args=[self.viewpoint.pk])
        )

    def test_viewpoint_delete_anonymous(self):
        response = self._viewpoint_delete()
        # User is not authenticated
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_viewpoint_delete_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_delete()
        # User doesn't have permission
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_delete_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )
        response = self._viewpoint_delete()
        # User have permission
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def _viewpoint_update(self):
        return self.client.patch(
            reverse(
                "terra_opp:viewpoint-detail",
                args=[self.viewpoint_with_accepted_picture.pk],
            ),
            {
                "label": "test",
                "properties": {"test_update": "ok"},
                "point": {"type": "Point", "coordinates": [0.0, 1.0]},
            },
            format="json",
        )

    def test_viewpoint_update_anonymous(self):
        response = self._viewpoint_update()
        # User is not authenticated
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_viewpoint_update_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_update()
        # User is authenticated but doesn't have permission to update the
        # viewpoint.
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_update_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )

        response = self._viewpoint_update()

        # User is authenticated and have permission to update the viewpoint.
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # Check if the viewpoint is correctly updated
        viewpoint = Viewpoint.objects.get(pk=self.viewpoint_with_accepted_picture.pk)
        self.assertEqual(response.data["label"], viewpoint.label)
        self.assertEqual(
            response.data["properties"]["test_update"],
            viewpoint.properties["test_update"],
        )

        # Check if the viewpoint's feature is correctly updated
        feature = Feature.objects.get(pk=self.viewpoint_with_accepted_picture.point.pk)
        self.assertEqual(response.data["label"], feature.properties["viewpoint_label"])
        self.assertEqual(
            self.viewpoint_with_accepted_picture.pk, feature.properties["viewpoint_id"]
        )
        self.assertEqual(
            response.data["point"]["coordinates"],
            [feature.geom.coords[0], feature.geom.coords[1]],
        )

    def test_add_picture_on_viewpoint_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )

        # We create a more recent picture
        date = timezone.datetime(2019, 1, 1, tzinfo=timezone.utc)

        response = self.client.get(
            reverse(
                "terra_opp:viewpoint-detail",
                args=[
                    self.viewpoint_with_accepted_picture.pk,
                ],
            ),
        )
        # Before last accepted date should be in 2018
        self.assertEqual(
            timezone.datetime(2018, 1, 1, tzinfo=timezone.utc),
            dateparse.parse_datetime(response.json()["last_accepted_picture_date"]),
        )

        file = SimpleUploadedFile(
            name="test.jpg",
            content=open(
                "terra_opp/tests/placeholder.jpg",
                "rb",
            ).read(),
            content_type="image/jpeg",
        )
        picture = Picture.objects.create(
            viewpoint=self.viewpoint_with_accepted_picture,
            owner=self.user,
            date=date,
            file=file,
            state="accepted",
        )
        response = self.client.patch(
            reverse(
                "terra_opp:viewpoint-detail",
                args=[
                    self.viewpoint_with_accepted_picture.pk,
                ],
            ),
            {"picture_ids": [picture.id]},
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # New last picture date now
        self.assertEqual(
            date,
            dateparse.parse_datetime(response.json()["last_accepted_picture_date"]),
        )

        viewpoint = Viewpoint.objects.get(pk=self.viewpoint_with_accepted_picture.pk)
        self.assertEqual(1, viewpoint.pictures.count())
        self.assertIn(
            f"viewpoint_{self.viewpoint_with_accepted_picture.pk}/2019-01-01_00-00-00",
            viewpoint.pictures.latest().file.name,
        )

        feature = Feature.objects.get(pk=self.viewpoint_with_accepted_picture.point.pk)
        # Check if the feature has been updated after patching
        self.assertIn(file.name.split(".")[0], feature.properties["viewpoint_picture"])

    def test_add_older_picture_on_viewpoint_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_viewpoints",
            ]
        )

        # We create an older picture
        date = timezone.datetime(1950, 1, 1, tzinfo=timezone.utc)
        file = SimpleUploadedFile(
            name="test_older.jpg",
            content=open(
                "terra_opp/tests/placeholder.jpg",
                "rb",
            ).read(),
            content_type="image/jpeg",
        )
        picture = Picture.objects.create(
            viewpoint=self.viewpoint_with_accepted_picture,
            owner=self.user,
            date=date,
            file=file,
            state="accepted",
        )
        picture_ids = [
            pic.id for pic in self.viewpoint_with_accepted_picture.pictures.all()
        ]
        picture_ids.append(picture.id)
        response = self.client.patch(
            reverse(
                "terra_opp:viewpoint-detail",
                args=[
                    self.viewpoint_with_accepted_picture.pk,
                ],
            ),
            {"picture_ids": picture_ids},
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        viewpoint = Viewpoint.objects.get(pk=self.viewpoint_with_accepted_picture.pk)
        self.assertEqual(2, viewpoint.pictures.count())
        self.assertNotIn(file.name.split(".")[0], viewpoint.pictures.latest().file.name)

        feature = Feature.objects.get(pk=self.viewpoint_with_accepted_picture.point.pk)
        # Check that the feature has not been updated after patching
        self.assertNotIn(
            file.name.split(".")[0], feature.properties["viewpoint_picture"]
        )

    def test_ordering_in_list_view(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(reverse("terra_opp:viewpoint-list")).json()
        # Now test that viewpoints are ordered in chronological order
        first_viewpoint = Viewpoint.objects.get(id=data.get("results")[0]["id"])
        second_viewpoint = Viewpoint.objects.get(id=data.get("results")[1]["id"])
        self.assertTrue(first_viewpoint.created_at > second_viewpoint.created_at)

    def test_list_viewset_return_distinct_objects(self):
        # We add a more recent picture to the viewpoint
        date = timezone.datetime(2019, 1, 1, tzinfo=timezone.utc)
        file = SimpleUploadedFile(
            name="test.jpg",
            content=open(
                "terra_opp/tests/placeholder.jpg",
                "rb",
            ).read(),
            content_type="image/jpeg",
        )
        Picture.objects.create(
            viewpoint=self.viewpoint_with_accepted_picture,
            owner=self.user,
            date=date,
            file=file,
            state="accepted",
        )

        # Viewpoint should appears only once in the list
        data = self.client.get(reverse("terra_opp:viewpoint-list")).json()
        self.assertEqual(1, data.get("count"))

    def test_pdf_view_must_return_pdf_when_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse(
                "terra_opp:viewpoint-pdf",
                args=[self.viewpoint.pk],
            )
        )
        self.assertEqual(status.HTTP_200_OK, data.status_code)
        self.assertIn("application/pdf", data["Content-Type"])

    def test_options_request_on_zip_pictures_must_return_200(self):
        data = self.client.options(
            reverse(
                "terra_opp:viewpoint-zip-pictures",
                args=[
                    self.viewpoint_with_accepted_picture.pk,
                ],
            )
        )
        self.assertEqual(status.HTTP_200_OK, data.status_code)
        self.assertIn("application/zip", data["Content-Type"])

    def test_get_request_on_zip_pictures_must_return_a_zip_with_accepted_pictures(self):
        data = self.client.get(
            reverse(
                "terra_opp:viewpoint-zip-pictures",
                args=[
                    self.viewpoint_with_accepted_picture.pk,
                ],
            )
        )
        self.assertEqual(status.HTTP_200_OK, data.status_code)
        self.assertIn("application/zip", data["Content-Type"])
        self.assertEqual(1, len(data.data))

    def test_add_picture_on_viewpoint_must_update_feature_properties(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_pictures",
            ]
        )

        # should be equal to 1
        picture_count = self.viewpoint_with_accepted_picture.pictures.count()

        file = SimpleUploadedFile(
            name="add_picture_test.jpg",
            content=open(
                "terra_opp/tests/placeholder.jpg",
                "rb",
            ).read(),
            content_type="image/jpeg",
        )
        data = {
            "viewpoint": self.viewpoint_with_accepted_picture.pk,
            "date": timezone.datetime(2020, 8, 19, tzinfo=timezone.utc),
            "file": file,
            "state": "accepted",
        }
        # this request must create a new picture on the viewpoint and update it's feature properties
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(
            self.viewpoint_with_accepted_picture.pictures.count(), picture_count + 1
        )
        # Check if the feature has been updated after patching, so update the object from the DB before
        self.viewpoint_with_accepted_picture.refresh_from_db()
        self.assertIn(
            f"viewpoint_{self.viewpoint_with_accepted_picture.pk}/2020-08-19_00-00-00",
            self.viewpoint_with_accepted_picture.point.properties["viewpoint_picture"],
        )

    def test_add_picture_on_viewpoint_with_no_picture_must_update_feature_properties(
        self,
    ):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_pictures",
            ]
        )

        # should be equal to 0
        picture_count = self.viewpoint_without_picture.pictures.count()

        file = SimpleUploadedFile(
            name="add_picture_test.jpg",
            content=open(
                "terra_opp/tests/placeholder.jpg",
                "rb",
            ).read(),
            content_type="image/jpeg",
        )
        data = {
            "viewpoint": self.viewpoint_without_picture.pk,
            "date": timezone.datetime(2020, 8, 19, tzinfo=timezone.utc),
            "file": file,
            "state": "accepted",
        }
        # this request must create a new picture on the viewpoint and update it's feature properties
        response = self.client.post(
            reverse("terra_opp:picture-list"),
            data,
            format="multipart",
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(
            self.viewpoint_without_picture.pictures.count(), picture_count + 1
        )
        # Check if the feature has been updated after patching, so update the object from the DB before
        self.viewpoint_without_picture.refresh_from_db()
        self.assertIn(
            f"viewpoint_{self.viewpoint_without_picture.pk}/2020-08-19_00-00-00",
            self.viewpoint_without_picture.point.properties["viewpoint_picture"],
        )

    def test_update_picture_on_viewpoint_must_update_feature_properties(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_pictures",
            ]
        )

        file = SimpleUploadedFile(
            name="another_placeholder.jpg",
            content=open(
                "terra_opp/tests/another_placeholder.jpg",
                "rb",
            ).read(),
            content_type="image/jpeg",
        )
        data = {
            "file": file,
        }
        # this request must create a new picture on the viewpoint and update it's feature properties
        response = self.client.patch(
            reverse(
                "terra_opp:picture-detail",
                args=[self.viewpoint_with_accepted_picture.pictures.latest().pk],
            ),
            data,
            format="multipart",
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # Check if the feature has been updated after patching, so update the object from the DB before
        self.viewpoint_with_accepted_picture.refresh_from_db()
        self.assertIn(
            f"viewpoint_{self.viewpoint_with_accepted_picture.pk}/2018-01-01_00-00-00",
            self.viewpoint_with_accepted_picture.point.properties["viewpoint_picture"],
        )

    def test_delete_picture_on_viewpoint_must_update_feature_properties(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_pictures",
            ]
        )

        PictureFactory(
            viewpoint=self.viewpoint_with_accepted_picture,
            date=timezone.datetime(2020, 8, 20, tzinfo=timezone.utc),
        )
        picture_count = self.viewpoint_with_accepted_picture.pictures.count()
        before_last_picture = self.viewpoint_with_accepted_picture.pictures.all()[1]

        # this request must delete the picture on the viewpoint and update it's feature properties
        response = self.client.delete(
            reverse(
                "terra_opp:picture-detail",
                args=[self.viewpoint_with_accepted_picture.pictures.latest().pk],
            ),
        )
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(
            self.viewpoint_with_accepted_picture.pictures.count(), picture_count - 1
        )
        # Check if the feature has been updated after patching, so update the object from the DB before
        self.viewpoint_with_accepted_picture.refresh_from_db()
        self.assertIn(
            before_last_picture.file.name.split(".")[0],
            self.viewpoint_with_accepted_picture.point.properties["viewpoint_picture"],
        )

    def test_delete_the_only_available_picture_on_viewpoint_must_update_feature_properties(
        self,
    ):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(
            [
                "can_manage_pictures",
            ]
        )

        # The viewpoint must only have a single available picture for this test
        self.assertEqual(1, self.viewpoint_with_accepted_picture.pictures.count())

        # This request must delete the only available picture on the viewpoint.
        response = self.client.delete(
            reverse(
                "terra_opp:picture-detail",
                args=[self.viewpoint_with_accepted_picture.pictures.latest().pk],
            ),
        )
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, self.viewpoint_with_accepted_picture.pictures.count())
        # Check if the feature has been updated after patching, so update the object from the DB before
        self.viewpoint_with_accepted_picture.refresh_from_db()
        self.assertFalse(
            "viewpoint_picture" in self.viewpoint_with_accepted_picture.point.properties
        )

    def test_only_active_viewpoint_retrieve(self):
        active_viewpoint = ViewpointFactory(
            label="Active viewpoint",
            active=True,
            pictures__state="accepted",
        )
        inactive_viewpoint = ViewpointFactory(
            label="Unactive viewpoint",
            active=False,
            pictures__state="accepted",
        )
        response = self.client.get(reverse("terra_opp:viewpoint-active"))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        active_viewpoint_count = (
            Viewpoint.objects.with_accepted_pictures().filter(active=True).count()
        )
        data = response.json()

        self.assertEqual(active_viewpoint_count, data["count"])
        self.assertNotIn(inactive_viewpoint.id, [d["id"] for d in data["results"]])
        self.assertIn(active_viewpoint.id, [d["id"] for d in data["results"]])
