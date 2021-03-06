from pprint import pformat

import coreapi
import coreschema
from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import Q
from django_filters import FilterSet
from django_filters.rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend
from url_filter.integrations.drf import DjangoFilterBackend

from .models import Viewpoint


class CampaignFilterBackend(BaseFilterBackend):
    """
    Filters for campaigns
    """

    def get_schema_fields(self, view):
        super().get_schema_fields(view)
        choices = {
            settings.TROPP_STATES.DRAFT: 'Incomplete metadata',
            settings.TROPP_STATES.SUBMITTED: 'Pending validation',
            settings.TROPP_STATES.REFUSED: 'Refused',
            settings.TROPP_STATES.ACCEPTED: 'Validated',
        }
        return [
            coreapi.Field(
                name='status',
                required=False,
                location='query',
                schema=coreschema.Boolean(
                    title="Campaign status",
                    description="0 for closed campaign, 1 for ongoing campaign"
                ),
            ),
            coreapi.Field(
                name='picture_status',
                required=False,
                location='query',
                schema=coreschema.Enum(
                    choices,
                    description=str(pformat(choices)),
                    title="Picture status",
                )
            )
        ]

    def filter_queryset(self, request, queryset, view):
        STATES = settings.TROPP_STATES
        status = request.GET.get('status', None)
        if status is not None:
            try:
                status = bool(int(status))
            except ValueError:
                raise ValidationError
            if status:
                queryset = queryset.filter(
                    viewpoints__pictures__state=STATES.ACCEPTED
                )
            else:
                queryset = queryset.exclude(
                    Q(viewpoints__pictures__state=STATES.ACCEPTED)
                )

        picture_status = request.GET.get('picture_status', None)
        if picture_status is not None:
            try:
                picture_status = int(picture_status)
                assert picture_status in STATES.CHOICES_DICT
            except (AssertionError, ValueError):
                raise ValidationError
            queryset = queryset.filter(
                viewpoints__pictures__state=picture_status
            )

        return queryset


class JsonFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            search_key = f'properties__{field["json_key"]}'
            if field['type'] == 'many':
                search_item = request.GET.getlist(f'{search_key}')
            else:
                search_item = request.GET.get(search_key)
            if search_item:
                if field['type'] == 'text':
                    # Full text search
                    queryset = queryset.annotate(**{
                        key: KeyTextTransform(field['json_key'], 'properties')
                    }).filter(**{f'{key}__icontains': search_item})
                else:
                    # Search on element
                    queryset = queryset.filter(**{
                        f'{search_key}__contains': search_item
                    })
        return queryset

    def get_schema_fields(self, view):
        fields = []
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            if field['type'] == 'many':
                klass = coreschema.Array
            else:
                klass = coreschema.String
            description = f"{key.capitalize()} property ({field['type']})"
            fields.append(
                coreapi.Field(
                    name=f'properties__{field["json_key"]}',
                    required=False,
                    location='query',
                    schema=klass(
                        title=f"{key.capitalize()} property",
                        description=description,
                    ),
                )
            )
        return super().get_schema_fields(view)


class ViewpointFilterSet(FilterSet):
    city = filters.CharFilter(field_name='city__label', lookup_expr='exact')
    themes = filters.CharFilter(field_name='themes__label', lookup_expr='exact')
    date_from = filters.DateFilter(field_name='pictures__date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='pictures__date', lookup_expr='lte')

    class Meta:
        model = Viewpoint
        fields = ['city', 'themes', 'date_from', 'date_to']


class SchemaAwareDjangoFilterBackend(DjangoFilterBackend):
    def get_schema_fields(self, view):
        """
        Get coreapi filter definitions

        Returns all schemas defined in filter_fields_schema attribute.
        """
        super().get_schema_fields(view)
        return getattr(view, 'filter_fields_schema', [])
