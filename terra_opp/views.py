import io
import operator
from functools import reduce

import coreapi
import coreschema
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields.jsonb import KeyTransform
from django.core.cache import cache
from django.db.models import Prefetch
from django.db import models
from django.template import loader
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, renderers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from .filters import (
    CampaignFilterBackend,
    JsonFilterBackend,
    ViewpointFilterSet,
    SchemaAwareDjangoFilterBackend,
    PictureFilterSet,
)
from .models import Campaign, City, Picture, Theme, Viewpoint
from .pagination import RestPageNumberPagination
from .point_utilities import remove_point_thumbnail, update_point_properties
from .renderers import PdfRenderer, ZipRenderer, write_pdf
from . import permissions

from .serializers import (
    CampaignSerializer,
    RoCampaignSerializer,
    ListCampaignNestedSerializer,
    PictureSerializer,
    SimpleAuthenticatedViewpointSerializer,
    SimpleViewpointSerializer,
    ViewpointSerializerWithPicture,
    PhotographSerializer,
    CitySerializer,
    ThemeSerializer,
)


class CampaignNotFound(APIException):
    status_code = 400
    default_detail = "Can't found any valid campaign to add picture"
    default_code = "campaign_not_found"


class PictureAlreadyExists(APIException):
    status_code = 400
    default_detail = "Picture already exists for this viewpoint in that campaign"
    default_code = "picture_already_exists"


class ViewpointViewSet(viewsets.ModelViewSet):
    serializer_class = ViewpointSerializerWithPicture
    permission_classes = [
        permissions.ViewpointPermission,
    ]
    filter_backends = (
        SearchFilter,
        SchemaAwareDjangoFilterBackend,
        JsonFilterBackend,
        DjangoFilterBackend,
    )
    filterset_class = ViewpointFilterSet
    filter_fields_schema = [
        coreapi.Field(
            name="pictures__identifier",
            required=False,
            location="query",
            schema=coreschema.Integer(
                title="Picture identifier",
                description="Picture identifier to filter on",
            ),
        ),
        coreapi.Field(
            name="pictures__owner__uuid",
            required=False,
            location="query",
            schema=coreschema.Integer(
                title="Photographer uuid",
                description="Photographer uuid to filter on",
            ),
        ),
    ]
    filter_fields = ["pictures", "active"]
    search_fields = ("label", "id")
    pagination_class = RestPageNumberPagination
    template_name = "terra_opp/viewpoint_pdf.html"

    def perform_create(self, serializer):
        serializer.save()
        update_point_properties(serializer.instance, self.request)

    def perform_update(self, serializer):
        serializer.save()
        update_point_properties(serializer.instance, self.request)

    def perform_destroy(self, instance):
        instance.point.delete()
        instance.delete()
        # FIXME This may be better if done directly in geostore
        # FIXME Try to be more precise and delete only the related feature's tile in cache
        cache.delete("tile_cache_*")  # delete all the cached tiles

    def filter_queryset(self, queryset):
        # We must reorder the queryset here because initial filtering in
        # viewpoint model is not done right see
        # https://github.com/encode/django-rest-framework/issues/1717
        return super().filter_queryset(queryset).order_by("-created_at")

    def get_queryset(self):
        # unauthenticated user not allowed to access archived viewpoint
        qs = Viewpoint.objects.with_accepted_pictures().filter(active=True)
        if self.request.user.is_authenticated:
            qs = Viewpoint.objects.all().distinct()

        pictures_qs = Picture.objects.order_by("-created_at")

        return (
            qs.select_related("point", "city")
            .prefetch_related(
                "pictures",
                "related",
                Prefetch("pictures", queryset=pictures_qs, to_attr="_ordered_pics"),
                "themes",
            )
            .annotate(
                last_accepted_picture_date=models.Max("pictures__date"),
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            if self.request.user.is_anonymous:
                return SimpleViewpointSerializer
            return SimpleAuthenticatedViewpointSerializer
        return ViewpointSerializerWithPicture

    @action(detail=False)
    def filters(self, request, *args, **kwargs):
        filter_values = {}
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            data = None
            transform = KeyTransform(field["json_key"], "properties")
            queryset = (
                Viewpoint.objects.annotate(**{key: transform})
                .exclude(**{f"{key}__isnull": True})
                .values_list(key, flat=True)
            )
            if field["type"] == "single":
                # Dedupe and sort with SQL
                data = queryset.order_by(key).distinct(key)
            elif field["type"] == "many":
                # Dedupe and sort programmatically
                data = list(queryset)
                if data:
                    data = set(reduce(operator.concat, data))
                    data = sorted(data, key=str.lower)
            if data is not None:
                filter_values[key] = data

        filter_values["photographers"] = PhotographSerializer(
            get_user_model().objects.filter(pictures__isnull=False).distinct(),
            many=True,
        ).data

        # FIXME We may want to set all cities and themes as uniques directly in the model?
        filter_values["cities"] = (
            City.objects.exclude(label__isnull=True)
            .exclude(label__exact="")
            .distinct()
            .order_by(
                "label",
            )
            .values_list(
                "label",
                flat=True,
            )
        )
        filter_values["themes"] = (
            Theme.objects.exclude(label__isnull=True)
            .exclude(
                label__exact="",
            )
            .distinct()
            .order_by(
                "label",
            )
            .values_list(
                "label",
                flat=True,
            )
        )

        return Response(filter_values)

    @method_decorator(cache_page(60 * 5))
    @action(
        detail=True,
        methods=[
            "get",
        ],
        renderer_classes=[ZipRenderer],
        url_path="zip-pictures",
    )
    def zip_pictures(self, request, *args, **kwargs):
        qs = (
            self.get_object()
            .pictures.filter(
                state="accepted",
            )
            .only("file")
        )
        return Response([p.file for p in qs])

    @action(
        detail=True,
        renderer_classes=[renderers.TemplateHTMLRenderer],
    )
    def preview(self, request, *args, **kwargs):
        properties_set = settings.TROPP_VIEWPOINT_PROPERTIES_SET["pdf"]
        return Response(
            {
                "viewpoint": self.get_object(),
                "properties_set": properties_set,
            },
            template_name="terra_opp/viewpoint_pdf.html",
        )

    @method_decorator(cache_page(60 * 5))
    @action(
        detail=True,
        methods=[
            "get",
        ],
        renderer_classes=[PdfRenderer],
    )
    def pdf(self, request, *args, **kwargs):
        properties_set = settings.TROPP_VIEWPOINT_PROPERTIES_SET["pdf"]
        return Response(
            {
                "viewpoint": self.get_object(),
                "properties_set": properties_set,
            }
        )

    @action(detail=False, methods=["get"])
    def active(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(active=True)
        qs_filtered = self.filter_queryset(qs)
        page = self.paginate_queryset(qs_filtered)

        if page is not None:
            serializer = SimpleViewpointSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SimpleViewpointSerializer(qs_filtered, many=True)
        return Response(serializer.data)


class PictureViewSet(viewsets.ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [
        permissions.PicturePermission,
    ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = PictureFilterSet
    pagination_class = RestPageNumberPagination

    def perform_create(self, serializer):
        if self.request.user.has_terra_perm("can_manage_pictures"):
            state = Picture.ACCEPTED
            owner = serializer.validated_data.get("owner")
            if not owner:
                owner = self.request.user
            serializer.save(state=state, owner=owner)
            update_point_properties(serializer.instance.viewpoint, self.request)

        elif self.request.user.has_terra_perm("can_add_pictures"):
            campaign = None
            viewpoint = serializer.validated_data.get("viewpoint")

            if "campaign" not in serializer.validated_data:
                # If no campaign specified we try to found one
                try:
                    campaign = Campaign.objects.get(
                        assignee=self.request.user,
                        state=Campaign.STARTED,
                        viewpoints=viewpoint,
                    )
                except Campaign.DoesNotExist:
                    raise CampaignNotFound()
            else:
                # Verify whether specified campaign exists
                campaign = serializer.validated_data.pop("campaign")
                try:
                    Campaign.objects.get(
                        id=campaign.id,
                        assignee=self.request.user,
                        state=Campaign.STARTED,
                        viewpoints=viewpoint,
                    )
                except Campaign.DoesNotExist:
                    raise CampaignNotFound()

            # Check whether the picture already exists for this viewpoint/campaign
            if Picture.objects.filter(viewpoint=viewpoint, campaign=campaign).exists():
                raise PictureAlreadyExists()

            serializer.save(owner=self.request.user, campaign=campaign)
            update_point_properties(serializer.instance.viewpoint, self.request)

    def perform_update(self, serializer):
        if self.request.user.has_terra_perm("can_manage_pictures"):
            serializer.save()
            update_point_properties(serializer.instance.viewpoint, self.request)

        elif self.request.user.has_terra_perm("can_add_pictures"):
            new_state = serializer.validated_data["state"]
            if new_state not in [
                Picture.DRAFT,
                Picture.SUBMITTED,
            ]:
                new_state = Picture.DRAFT
            # For self as user and draft state
            serializer.save(owner=self.request.user, state=new_state)
            update_point_properties(serializer.instance.viewpoint, self.request)

    def perform_destroy(self, instance):
        remove_point_thumbnail(instance, self.request)
        instance.delete()


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.with_stats()
    permission_classes = [
        permissions.CampaignPermission,
    ]
    http_method_names = ["get", "post", "put", "delete", "options"]
    filter_backends = (CampaignFilterBackend, SearchFilter)
    search_fields = ("label",)
    pagination_class = RestPageNumberPagination

    def filter_queryset(self, queryset):
        # We must reorder the queryset here because initial filtering in
        # viewpoint model is not done right see
        # https://github.com/encode/django-rest-framework/issues/1717
        return super().filter_queryset(queryset).order_by("-start_date", "-created_at")

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if self.action == "retrieve":
            qs = qs.prefetch_related("pictures")

        # Filter only on assigned campaigns for photographs
        if self.action == "list" and not user.has_terra_perm("can_manage_campaigns"):
            return qs.filter(
                assignee=user, state__in=[Campaign.STARTED, Campaign.CLOSED]
            )

        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ListCampaignNestedSerializer

        # Serializer without stats for update
        if self.action in ["create", "update"]:
            return CampaignSerializer

        return RoCampaignSerializer

    @method_decorator(cache_page(60 * 5))
    @action(
        detail=True,
        renderer_classes=[ZipRenderer],
    )
    def all_sheets(self, request, *args, **kwargs):
        viewpoints = self.get_object().viewpoints.all()

        pdfs = []

        for viewpoint in viewpoints:
            template = loader.select_template(["terra_opp/viewpoint_pdf.html"])
            html = template.render(
                context={
                    "viewpoint": viewpoint,
                    "properties_set": settings.TROPP_VIEWPOINT_PROPERTIES_SET["pdf"],
                }
            )

            pdf_bytes = write_pdf(request, html)

            stream = io.BytesIO(pdf_bytes)
            stream.name = f"viewpoint_{viewpoint.pk}.pdf"

            pdfs.append(stream)

        return Response(pdfs)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    http_method_names = ["get", "post", "put", "delete", "options"]
    filter_backends = (SearchFilter,)
    serializer_class = CitySerializer
    search_fields = ("label",)
    pagination_class = RestPageNumberPagination


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    http_method_names = ["get", "post", "put", "delete", "options"]
    filter_backends = (SearchFilter,)
    serializer_class = ThemeSerializer
    search_fields = ("label",)
    pagination_class = RestPageNumberPagination
