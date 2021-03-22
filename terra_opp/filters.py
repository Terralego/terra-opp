from pprint import pformat

import coreapi
import coreschema
from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django_filters import FilterSet
from django_filters.rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend
from url_filter.integrations.drf import DjangoFilterBackend

from .models import Viewpoint, Picture, Campaign


class CampaignFilterBackend(BaseFilterBackend):
    """
    Filters for campaigns
    """

    def get_schema_fields(self, view):
        super().get_schema_fields(view)
        return [
            coreapi.Field(
                name="status",
                required=False,
                location="query",
                schema=coreschema.Boolean(
                    title="Campaign status",
                    description="0 for closed campaign, 1 for ongoing campaign",
                ),
            ),
            coreapi.Field(
                name="picture_state",
                required=False,
                location="query",
                schema=coreschema.Enum(
                    Picture.STATES,
                    description=str(pformat(Picture.STATES)),
                    title="Picture status",
                ),
            ),
        ]

    def filter_queryset(self, request, queryset, view):
        status = request.GET.get("status", None)
        if status is not None:
            try:
                assert status in [s[0] for s in Campaign.STATES]
            except ValueError:
                raise ValidationError
            queryset = queryset.filter(state=status)

        picture_status = request.GET.get("picture_status", None)
        if picture_status is not None:
            try:
                assert picture_status in [s[0] for s in Picture.STATES]
            except (AssertionError, ValueError):
                raise ValidationError
            queryset = queryset.filter(viewpoints__pictures__state=picture_status)

        return queryset


class JsonFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            search_key = f'properties__{field["json_key"]}'
            if field["type"] == "many":
                search_item = request.GET.getlist(f"{search_key}")
            else:
                search_item = request.GET.get(search_key)
            if search_item:
                if field["type"] == "text":
                    # Full text search
                    queryset = queryset.annotate(
                        **{key: KeyTextTransform(field["json_key"], "properties")}
                    ).filter(**{f"{key}__icontains": search_item})
                else:
                    # Search on element
                    queryset = queryset.filter(
                        **{f"{search_key}__contains": search_item}
                    )
        return queryset

    def get_schema_fields(self, view):
        fields = []
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            if field["type"] == "many":
                klass = coreschema.Array
            else:
                klass = coreschema.String
            description = f"{key.capitalize()} property ({field['type']})"
            fields.append(
                coreapi.Field(
                    name=f'properties__{field["json_key"]}',
                    required=False,
                    location="query",
                    schema=klass(
                        title=f"{key.capitalize()} property",
                        description=description,
                    ),
                )
            )
        return super().get_schema_fields(view)


class ViewpointFilterSet(FilterSet):
    city = filters.CharFilter(field_name="city__label", lookup_expr="exact")
    themes = filters.CharFilter(field_name="themes__label", lookup_expr="exact")
    date_from = filters.DateFilter(field_name="pictures__date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="pictures__date", lookup_expr="lte")

    class Meta:
        model = Viewpoint
        fields = ["city", "themes", "date_from", "date_to", "active"]


class PictureFilterSet(FilterSet):
    # owner_id = filters.IntegerFilter(field_name="owner", lookup_expr="exact")

    class Meta:
        model = Picture
        fields = ["owner"]


class SchemaAwareDjangoFilterBackend(DjangoFilterBackend):
    def get_schema_fields(self, view):
        """
        Get coreapi filter definitions

        Returns all schemas defined in filter_fields_schema attribute.
        """
        super().get_schema_fields(view)
        return getattr(view, "filter_fields_schema", [])
