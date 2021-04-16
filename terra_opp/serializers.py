from typing import Optional

from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from geostore import GeometryTypes
from geostore.models import Feature, Layer
from rest_framework import serializers, fields
from rest_framework_gis.fields import GeometryField
from datastore.models import RelatedDocument
from datastore.serializers import RelatedDocumentUrlSerializer
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import Campaign, City, Picture, Theme, Viewpoint

UserModel = get_user_model()


class PermissiveImageFieldSerializer(VersatileImageFieldSerializer):
    def get_attribute(self, instance):
        try:
            return super().get_attribute(instance)
        except (AttributeError, ObjectDoesNotExist):
            # Will silence any NoneType or failing query on attribute
            return None


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = "__all__"


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = "__all__"


class SimpleViewpointSerializer(serializers.ModelSerializer):
    picture = VersatileImageFieldSerializer("terra_opp")
    point = GeometryField(source="point.geom")

    class Meta:
        model = Viewpoint
        fields = (
            "id",
            "label",
            "picture",
            "point",
            "active",
        )


class LabelSlugRelatedField(serializers.SlugRelatedField):
    _model = None

    def to_internal_value(self, data):
        self._model.objects.get_or_create(label=data, defaults={"label": data})
        return super().to_internal_value(data)


class CityLabelSlugRelatedField(LabelSlugRelatedField):
    _model = City


class ThemeLabelSlugRelatedField(LabelSlugRelatedField):
    _model = Theme


class SimpleAuthenticatedViewpointSerializer(SimpleViewpointSerializer):
    city = CityLabelSlugRelatedField(
        slug_field="label",
        queryset=City.objects.all(),
        required=False,
        allow_null=False,
    )
    themes = ThemeLabelSlugRelatedField(
        slug_field="label", many=True, queryset=Theme.objects.all(), required=False
    )
    last_accepted_picture_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Viewpoint
        fields = (
            "id",
            "label",
            "picture",
            "point",
            "properties",
            "city",
            "themes",
            "active",
            "last_accepted_picture_date",
        )


class PhotographSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ("uuid", "email", "properties")
        read_only_fields = (
            "uuid",
            UserModel.USERNAME_FIELD,
        )


class PictureSerializer(serializers.ModelSerializer):
    owner_id = serializers.PrimaryKeyRelatedField(
        source="owner",
        queryset=UserModel.objects.all(),
        required=False,
        many=False,
    )
    owner = PhotographSerializer(read_only=True)
    file = VersatileImageFieldSerializer("terra_opp")
    identifier = serializers.CharField(read_only=True)

    class Meta:
        model = Picture
        fields = "__all__"


class SimplePictureSerializer(PictureSerializer):
    class Meta:
        model = Picture
        fields = ("id", "date", "file", "owner", "properties", "state", "identifier")


class CampaignPictureSerializer(PictureSerializer):
    class Meta:
        model = Picture
        fields = ("id", "date", "state", "viewpoint")


class ViewpointSerializerWithPicture(serializers.ModelSerializer):
    picture_ids = serializers.PrimaryKeyRelatedField(
        source="pictures",
        queryset=Picture.objects.all(),
        required=False,
        many=True,
    )
    pictures = SimplePictureSerializer(many=True, read_only=True)
    last_accepted_picture_date = serializers.DateTimeField(read_only=True)
    related = RelatedDocumentUrlSerializer(many=True, required=False)
    point = GeometryField(source="point.geom")
    city = CityLabelSlugRelatedField(
        slug_field="label",
        queryset=City.objects.all(),
        required=False,
        allow_null=False,
    )
    themes = ThemeLabelSlugRelatedField(
        slug_field="label", many=True, queryset=Theme.objects.all(), required=False
    )

    class Meta:
        model = Viewpoint
        fields = (
            "id",
            "label",
            "properties",
            "point",
            "picture_ids",
            "pictures",
            "related",
            "city",
            "themes",
            "active",
            "last_accepted_picture_date",
        )

    @transaction.atomic
    def create(self, validated_data):
        related_docs = validated_data.pop("related", None)
        point_data = validated_data.pop("point", None)

        # Get or create layer
        layer, created = Layer.objects.get_or_create(
            pk=settings.TROPP_OBSERVATORY_LAYER_PK,
            defaults={
                "geom_type": GeometryTypes.Point,
                "id": settings.TROPP_OBSERVATORY_LAYER_PK,
            },
        )

        # Create feature
        feature = Feature.objects.create(
            geom=point_data.get("geom"),
            layer_id=settings.TROPP_OBSERVATORY_LAYER_PK,
            properties={},
        )
        validated_data.setdefault("point", feature)

        # Get or create city
        city_label = validated_data.pop("city", None)
        city, created = City.objects.get_or_create(
            label=city_label,
            defaults={
                "label": city_label,
            },
        )
        validated_data.setdefault("city", city)

        # Handle themes
        themes_labels = validated_data.pop("themes", None)
        if themes_labels:
            theme_list = []
            for theme_label in themes_labels:
                theme, created = Theme.objects.get_or_create(
                    label=theme_label,
                    defaults={
                        "label": theme_label,
                    },
                )
                theme_list.append(theme)
            validated_data.setdefault("themes", theme_list)

        instance = super().create(validated_data)

        # Handle related docs
        self.handle_related_documents(instance, related_docs)

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        point_data = validated_data.pop("point", None)
        if point_data:
            feature = instance.point
            feature.geom = point_data.get("geom")
            feature.save()

        # Remove pictures no longer associated with viewpoint
        if "pictures" in validated_data:
            picture_ids = [p.pk for p in validated_data["pictures"]]
            instance.pictures.exclude(pk__in=picture_ids).delete()

        related_docs = validated_data.pop("related", None)
        self.handle_related_documents(instance, related_docs)

        return super().update(instance, validated_data)

    @staticmethod
    def handle_related_documents(instance: Viewpoint, related_docs: Optional[list]):
        if related_docs is not None:
            # Remove stale
            instance.related.exclude(key__in=[r["key"] for r in related_docs]).delete()
            for related in related_docs:
                file = related["document"]
                extension = file.content_type.split("/")[1]
                file.name = f"{related['key']}.{extension}"
                try:
                    existing = instance.related.get(key=related["key"])
                    existing.document = file
                    existing.save()
                except RelatedDocument.DoesNotExist:
                    RelatedDocument(**related, linked_object=instance).save()


class ViewpointLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = ("id", "label")


# Writable serializer
class CampaignSerializer(serializers.ModelSerializer):
    start_date = fields.DateField(input_formats=["%Y-%m-%d"])
    owner = serializers.PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = Campaign
        fields = "__all__"


# ReadOnly serializer
class RoCampaignSerializer(CampaignSerializer):
    pictures = CampaignPictureSerializer(many=True, read_only=True)
    statistics = serializers.SerializerMethodField()

    # Format stats as dict
    def get_statistics(self, obj):
        return dict(
            total=obj.viewpoints_total,
            submited=obj.pictures_submited,
            accepted=obj.pictures_accepted,
            missing=obj.pictures_missing,
        )


# List serializer
class ListCampaignNestedSerializer(RoCampaignSerializer):
    class Meta(CampaignSerializer.Meta):
        model = Campaign
        fields = (
            "id",
            "label",
            "start_date",
            "assignee",
            "statistics",
            "state",
        )
