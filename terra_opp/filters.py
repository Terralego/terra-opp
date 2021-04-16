from pprint import pformat

import coreapi
import coreschema
from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django_filters import FilterSet
from django_filters.rest_framework import filters
from rest_framework.filters import BaseFilterBackend
from url_filter.integrations.drf import DjangoFilterBackend
from rest_framework.exceptions import APIException

from .models import Viewpoint, Picture, Campaign


class BadFilter(APIException):
    status_code = 400
    default_detail = "Bad filter"
    default_code = "bad_filter"


class CampaignFilterBackend(BaseFilterBackend):
    """
    Filters for campaigns
    """

    def get_schema_fields(self, view):
        super().get_schema_fields(view)
        return [
            coreapi.Field(
                name="state",
                required=False,
                location="query",
                schema=coreschema.Boolean(
                    title="Campaign state",
                    description="'draft', 'started' or 'closed'",
                ),
            ),
            coreapi.Field(
                name="picture__state",
                required=False,
                location="query",
                schema=coreschema.Enum(
                    Picture.STATES,
                    description=str(pformat(Picture.STATES)),
                    title="Picture state",
                ),
            ),
        ]

    def filter_queryset(self, request, queryset, view):
        state = request.GET.get("state", None)
        if state is not None:

            if state not in [s[0] for s in Campaign.STATES]:
                raise BadFilter("Bad filter value for campaign state")

            queryset = queryset.filter(state=state)

        pictures_state = request.GET.get("pictures__state", None)
        if pictures_state is not None:

            if pictures_state not in [s[0] for s in Picture.STATES]:
                raise BadFilter("Bad filter value for pictures state")

            queryset = queryset.filter(pictures__state=pictures_state)

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
    id = filters.CharFilter(field_name="id", lookup_expr="exact")
    city = filters.CharFilter(field_name="city__label", lookup_expr="exact")
    themes = filters.CharFilter(field_name="themes__label", lookup_expr="exact")
    city_id = filters.CharFilter(field_name="city", lookup_expr="exact")
    themes_id = filters.CharFilter(field_name="themes", lookup_expr="exact")
    date_from = filters.DateFilter(field_name="pictures__date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="pictures__date", lookup_expr="lte")
    last_picture = filters.DateFilter(
        field_name="last_accepted_picture_date", lookup_expr="lte"
    )

    class Meta:
        model = Viewpoint
        fields = [
            "id",
            "city",
            "themes",
            "city_id",
            "themes_id",
            "date_from",
            "date_to",
            "active",
            "last_picture",
        ]


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
