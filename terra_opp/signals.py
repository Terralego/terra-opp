from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import Picture, Viewpoint


@receiver(post_save, sender=Viewpoint)
def update_or_create_viewpoint(instance, **kwargs):
    """
    This signal is triggered after Viewpoint save (update or create). It will
    update its feature with the related viewpoint details.
    """
    point = instance.point
    point.properties = {
        'viewpoint_id': instance.id,
        'viewpoint_label': instance.label,
    }

    # Add any specified viewpoint property in the feature's properties
    for prop in settings.TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT:
        value = instance.properties.get(prop)
        if value is not None:
            point.properties[f'viewpoint_{prop}'] = value

    point.save()


@receiver(post_save, sender=Picture)
def update_or_create_picture(instance, **kwargs):
    viewpoint = instance.viewpoint
    point = viewpoint.point
    latest_picture = viewpoint.pictures.latest()

    # Add thumbnail representation in the feature's properties
    # only if this instance is newer than the latest picture
    if instance.date >= latest_picture.date:
        last_picture_sizes = VersatileImageFieldSerializer('terra_opp').to_representation(instance.file)
        point.properties['viewpoint_picture'] = (
            f"http://{Site.objects.get_current().domain}{last_picture_sizes['thumbnail']}"
        )
        point.save()
