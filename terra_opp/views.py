import operator
from functools import reduce

import coreapi
import coreschema
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields.jsonb import KeyTransform
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from terra_accounts.serializers import UserProfileSerializer
from terra_utils.filters import DateFilterBackend, SchemaAwareDjangoFilterBackend

from .filters import CampaignFilterBackend, JsonFilterBackend
from .models import Campaign, Picture, Viewpoint
from .pagination import RestPageNumberPagination
from .renderers import PdfRenderer, ZipRenderer
from .serializers import (
    CampaignSerializer,
    DetailAuthenticatedCampaignNestedSerializer,
    DetailCampaignNestedSerializer,
    ListCampaignNestedSerializer,
    PictureSerializer,
    SimpleAuthenticatedViewpointSerializer,
    SimpleViewpointSerializer,
    ViewpointSerializerWithPicture,
)
from .point_utilities import remove_point_thumbnail, update_point_properties


class ViewpointViewSet(viewsets.ModelViewSet):
    serializer_class = ViewpointSerializerWithPicture
    permission_classes = [
        permissions.DjangoModelPermissionsOrAnonReadOnly,
    ]
    filter_backends = (
        SearchFilter,
        SchemaAwareDjangoFilterBackend,
        DateFilterBackend,
        JsonFilterBackend,
    )
    filter_fields_schema = [
        coreapi.Field(
            name='pictures__id',
            required=False,
            location='query',
            schema=coreschema.Integer(
                title="Picture id",
                description="Picture id to filter on",
            ),
        ),
        coreapi.Field(
            name='pictures__owner__uuid',
            required=False,
            location='query',
            schema=coreschema.Integer(
                title="Photographer uuid",
                description="Photographer uuid to filter on",
            ),
        ),
    ]
    filter_fields = ['pictures']
    search_fields = ('label', )
    date_search_field = 'pictures__date__date'
    pagination_class = RestPageNumberPagination
    template_name = 'terra_opp/viewpoint_pdf.html'

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
        cache.delete('tile_cache_*')  # delete all the cached tiles

    def filter_queryset(self, queryset):
        # We must reorder the queryset here because initial filtering in
        # viewpoint model is not done right see
        # https://github.com/encode/django-rest-framework/issues/1717
        return super().filter_queryset(queryset).order_by('-created_at')

    def get_queryset(self):
        qs = Viewpoint.objects.with_accepted_pictures()
        if self.request.user.is_authenticated:
            qs = Viewpoint.objects.all().distinct()
        pictures_qs = Picture.objects.order_by('-created_at')
        return qs.select_related('point').prefetch_related(
            Prefetch('pictures', queryset=pictures_qs, to_attr='_ordered_pics')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.user.is_anonymous:
                return SimpleViewpointSerializer
            return SimpleAuthenticatedViewpointSerializer
        return ViewpointSerializerWithPicture

    @action(detail=False)
    def filters(self, request, *args, **kwargs):
        filter_values = {}
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            data = None
            transform = KeyTransform(field['json_key'], 'properties')
            queryset = (Viewpoint.objects
                        .annotate(**{key: transform})
                        .exclude(**{f"{key}__isnull": True})
                        .values_list(key, flat=True))
            if field['type'] == 'single':
                # Dedupe and sort with SQL
                data = queryset.order_by(key).distinct(key)
            elif field['type'] == 'many':
                # Dedupe and sort programmatically
                data = list(queryset)
                if data:
                    data = set(reduce(operator.concat, data))
                    data = sorted(data, key=str.lower)
            if data is not None:
                filter_values[key] = data

        filter_values['photographers'] = UserProfileSerializer(
            get_user_model().objects.filter(pictures__isnull=False).distinct(),
            many=True,
        ).data

        return Response(filter_values)

    @method_decorator(cache_page(60 * 5))
    @action(detail=True, methods=['get', ], renderer_classes=[ZipRenderer], url_path='zip-pictures')
    def zip_pictures(self, request, *args, **kwargs):
        qs = self.get_object().pictures.filter(
            state__gte=settings.TROPP_STATES.ACCEPTED,
        ).only('file')
        return Response([p.file for p in qs])

    @method_decorator(cache_page(60 * 5))
    @action(detail=True, methods=['get', ], renderer_classes=[PdfRenderer])
    def pdf(self, request, *args, **kwargs):
        properties_set = settings.TROPP_VIEWPOINT_PROPERTIES_SET['pdf']
        return Response({
            'viewpoint': self.get_object(),
            'properties_set': properties_set,
        })


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    http_method_names = ['get', 'post', 'put', 'delete', 'options']
    filter_backends = (CampaignFilterBackend, DateFilterBackend, SearchFilter)
    date_search_field = 'created_at'
    search_fields = ('label', )
    pagination_class = RestPageNumberPagination

    def get_queryset(self):
        # Filter only on assigned campaigns for photographs
        user = self.request.user
        pictures_qs = Picture.objects.order_by('-created_at')
        qs = super().get_queryset().prefetch_related(
            Prefetch('viewpoints__pictures', queryset=pictures_qs,
                     to_attr='ordered_pics')
        )
        if (self.action == 'list' and
                not user.has_perm('terra_opp.manage_all_campaigns')):
            return qs.filter(assignee=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def check_object_permissions(self, request, obj: Campaign):
        # Prevent acting on unassigned campaigns for photographs
        if (not request.user.has_perm('terra_opp.manage_all_campaigns') and
                obj.assignee != request.user):
            self.permission_denied(request)
        super().check_object_permissions(request, obj)

    def get_serializer_class(self):
        if self.action == 'list':
            return ListCampaignNestedSerializer
        if self.action == 'retrieve':
            if self.request.user.is_anonymous:
                return DetailCampaignNestedSerializer
            return DetailAuthenticatedCampaignNestedSerializer
        return CampaignSerializer


class PictureViewSet(viewsets.ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    pagination_class = RestPageNumberPagination

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        update_point_properties(serializer.instance.viewpoint, self.request)

    def perform_update(self, serializer):
        serializer.save()
        update_point_properties(serializer.instance.viewpoint, self.request)

    def perform_destroy(self, instance):
        remove_point_thumbnail(instance, self.request)
        instance.delete()
