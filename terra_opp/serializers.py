from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from geostore import GeometryTypes
from geostore.models import Feature, Layer
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from terra_accounts.serializers import UserProfileSerializer
from datastore.models import RelatedDocument
from datastore.serializers import RelatedDocumentSerializer
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import Campaign, Picture, Viewpoint

UserModel = get_user_model()


class PermissiveImageFieldSerializer(VersatileImageFieldSerializer):
    def get_attribute(self, instance):
        try:
            return super().get_attribute(instance)
        except (AttributeError, ObjectDoesNotExist):
            # Will silence any NoneType or failing query on attribute
            return None


class SimpleViewpointSerializer(serializers.ModelSerializer):
    picture = VersatileImageFieldSerializer('terra_opp')
    point = GeometryField(source='point.geom')

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'picture', 'point')


class SimpleAuthenticatedViewpointSerializer(SimpleViewpointSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'picture', 'point', 'status', 'properties')

    def get_status(self, obj):
        """
        :return: string (missing, draft, submitted, accepted)
        """
        # Get only pictures created for the campaign
        STATES = settings.TROPP_STATES
        try:
            last_pic = obj.ordered_pics[0]
            if last_pic.created_at < obj.created_at:
                return STATES.CHOICES_DICT[STATES.MISSING]
            return STATES.CHOICES_DICT[last_pic.state]
        except IndexError:
            return STATES.CHOICES_DICT[STATES.MISSING]


class CampaignSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Campaign
        fields = '__all__'


class DetailCampaignNestedSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')
    viewpoints = SimpleViewpointSerializer(many=True, read_only=True)

    class Meta(CampaignSerializer.Meta):
        model = Campaign
        fields = '__all__'


class DetailAuthenticatedCampaignNestedSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')
    viewpoints = SimpleAuthenticatedViewpointSerializer(many=True, read_only=True)

    class Meta(CampaignSerializer.Meta):
        model = Campaign
        fields = '__all__'


class ListCampaignNestedSerializer(CampaignSerializer):
    picture = PermissiveImageFieldSerializer(
        'terra_opp',
        source='viewpoints.first.pictures.first.file',
    )
    # Override to expose typed data
    statistics = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True,
    )
    status = serializers.BooleanField(read_only=True)

    class Meta(CampaignSerializer.Meta):
        model = Campaign
        fields = ('label', 'assignee', 'picture', 'statistics', 'status')


class PictureSerializer(serializers.ModelSerializer):
    owner = UserProfileSerializer(read_only=True)
    file = VersatileImageFieldSerializer('terra_opp')

    class Meta:
        model = Picture
        fields = '__all__'


class SimplePictureSerializer(PictureSerializer):
    class Meta:
        model = Picture
        fields = ('id', 'date', 'file', 'owner', 'properties')


class ViewpointSerializerWithPicture(serializers.ModelSerializer):
    picture_ids = serializers.PrimaryKeyRelatedField(
        source='pictures',
        queryset=Picture.objects.all(),
        required=False,
        many=True,
    )
    pictures = SimplePictureSerializer(many=True, read_only=True)
    related = RelatedDocumentSerializer(many=True, required=False)
    point = GeometryField(source='point.geom')

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'properties', 'point', 'picture_ids',
                  'pictures', 'related')

    def create(self, validated_data):
        related_docs = validated_data.pop('related', None)
        point_data = validated_data.pop('point', None)
        layer, created = Layer.objects.get_or_create(
            pk=settings.TROPP_OBSERVATORY_LAYER_PK,
            defaults={
                'geom_type': GeometryTypes.Point,
                'id': settings.TROPP_OBSERVATORY_LAYER_PK
            }
        )
        feature = Feature.objects.create(
            geom=point_data.get('geom'),
            layer_id=settings.TROPP_OBSERVATORY_LAYER_PK,
            properties={},
        )
        validated_data.setdefault('point', feature)

        instance = super().create(validated_data)
        self.handle_related_documents(instance, related_docs)
        return instance

    def update(self, instance, validated_data):
        point_data = validated_data.pop('point', None)
        if point_data:
            feature = instance.point
            feature.geom = point_data.get('geom')
            feature.save()

        # Remove pictures no longer associated with viewpoint
        if 'pictures' in validated_data:
            picture_ids = [p.pk for p in validated_data['pictures']]
            instance.pictures.exclude(pk__in=picture_ids).delete()

        related_docs = validated_data.pop('related', None)
        self.handle_related_documents(instance, related_docs)

        return super().update(instance, validated_data)

    @staticmethod
    def handle_related_documents(instance: Viewpoint,
                                 related_docs: Optional[list]):
        if related_docs is not None:
            # Remove stale
            instance.related.exclude(
                key__in=[r['key'] for r in related_docs]
            ).delete()
            for related in related_docs:
                file = related['document']
                extension = file.content_type.split('/')[1]
                file.name = f"{related['key']}.{extension}"
                try:
                    existing = instance.related.get(key=related['key'])
                    existing.document = file
                    existing.save()
                except RelatedDocument.DoesNotExist:
                    RelatedDocument(**related, linked_object=instance).save()


class ViewpointLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = ('id', 'label')
