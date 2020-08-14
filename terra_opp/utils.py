from django.conf import settings
from django.http import HttpRequest
from versatileimagefield.serializers import VersatileImageFieldSerializer

from terra_opp.models import Picture, Viewpoint


def update_point_properties(instance: Viewpoint):
    """
    Update the point properties of the given Viewpoint instance.
    The properties are the viewpoint's id and label, and all those defined in the
    TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT setting.

    :param Viewpoint instance: Viewpoint instance used to update its point properties
    """
    # TODO tests
    point = instance.point
    properties = {
        'viewpoint_id': instance.id,
        'viewpoint_label': instance.label,
    }
    # Merging the properties bellow in the ones already present in the point
    point.properties = {**point.properties, **properties}

    # Add any specified viewpoint property in the feature's properties
    for prop in settings.TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT:
        value = instance.properties.get(prop)
        if value is not None:
            point.properties[f'viewpoint_{prop}'] = value

    point.save()


def change_point_thumbnail(picture: Picture, context):
    """ Change the picture's point thumbnail """
    # TODO tests
    terra_opp_versatile_serializer = VersatileImageFieldSerializer('terra_opp')
    terra_opp_versatile_serializer._context = context
    last_picture_sizes = terra_opp_versatile_serializer.to_representation(picture.file)
    picture.viewpoint.point.properties['viewpoint_picture'] = last_picture_sizes['thumbnail']
    picture.viewpoint.point.save()


def update_point_thumbnail(picture: Picture, request: HttpRequest):
    """
    Update the point thumbnail of the given Picture instance only if the given picture is newer than the lastest
    picture on its related viewpoint. The request is mandatory as it will be used to determine the picture location.

    :param Picture picture: Picture instance used to update its related point thumbnail property.
    :param HttpRequest request: The original request instance.
    """
    # TODO tests
    latest_picture = picture.viewpoint.pictures.latest()

    if picture.date >= latest_picture.date:
        # The current picture is more recent than the latest one, so we need to update it
        change_point_thumbnail(picture, context={'request': request})


def remove_point_thumbnail(picture: Picture, request: HttpRequest):
    """
    Remove the point's thumbnail of the given Picture instance only if the picture was the latest. The request is
    mandatory as it will be used to determine the picture location.

    :param Picture picture: Picture instance used to update its related point thumbnail property.
    :param HttpRequest request: The original request instance.
    """
    # TODO tests
    latest_picture = picture.viewpoint.pictures.latest()

    if latest_picture == picture:
        # we need to update the point thumbnail
        new_latest_picture = picture.viewpoint.ordered_pics[1]
        change_point_thumbnail(new_latest_picture, context={'request': request})
