from django.http import HttpRequest
from versatileimagefield.serializers import VersatileImageFieldSerializer

from terra_opp.models import Picture


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
