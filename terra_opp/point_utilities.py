from PIL import Image
from django.conf import settings
from django.http import HttpRequest
from versatileimagefield.serializers import VersatileImageFieldSerializer
from terra_opp.models import Picture, Viewpoint


def update_point_properties(viewpoint: Viewpoint, request: HttpRequest):
    """
    Update the point properties of the given Viewpoint instance.
    The properties are the viewpoint's id and label, and all those defined in the
    TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT setting.

    :param Viewpoint viewpoint: Viewpoint instance used to update its point properties
    :param HttpRequest request: The original request instance.
    """
    point = viewpoint.point
    properties = {
        "viewpoint_id": viewpoint.id,
        "viewpoint_label": viewpoint.label,
        "viewpoint_city": viewpoint.city.label if viewpoint.city else "",
        "viewpoint_active": viewpoint.active,
    }
    # Merging the properties bellow in the ones already present in the point
    point.properties = {**point.properties, **properties}

    # Add thumbnail representation in the feature's properties
    if viewpoint.pictures.filter(state="accepted").exists():
        change_point_thumbnail(
            viewpoint.pictures.filter(state="accepted").latest(),
            context={"request": request},
        )

    # Add any specified viewpoint property in the feature's properties
    for prop in settings.TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT:
        value = viewpoint.properties.get(prop)
        if value is not None:
            point.properties[f"viewpoint_{prop}"] = value

    point.save()


def change_point_thumbnail(picture: Picture, context):
    """
    Change the point thumbnail of the given Picture instance. The context is mandatory as it will be used to determine
    the picture location.

    :param Picture picture: Picture instance used to update its related point thumbnail property.
    :param context: The context containing the original request instance.
    :return:
    """
    """ Change the picture's point thumbnail """

    terra_opp_versatile_serializer = VersatileImageFieldSerializer("terra_opp")
    terra_opp_versatile_serializer._context = context
    last_picture_sizes = terra_opp_versatile_serializer.to_representation(picture.file)

    # Use best image thumbnail
    with Image.open(picture.file) as pic:
        width, height = pic.size
        if width < height:
            picture.viewpoint.point.properties[
                "viewpoint_picture"
            ] = last_picture_sizes["thumbnail_vertical"]
        else:
            picture.viewpoint.point.properties[
                "viewpoint_picture"
            ] = last_picture_sizes["thumbnail"]

    picture.viewpoint.point.save()


def remove_point_thumbnail(picture: Picture, request: HttpRequest):
    """
    Remove and/or update the point's thumbnail of the given Picture instance only if the picture was the latest.
    The request is mandatory as it will be used to determine the picture location.

    :param Picture picture: Picture instance used to update its related point thumbnail property.
    :param HttpRequest request: The original request instance.
    """
    latest_picture = picture.viewpoint.pictures.latest()

    if latest_picture == picture and picture.viewpoint.pictures.count() > 1:
        # we need to update the point thumbnail
        new_latest_picture = picture.viewpoint.ordered_pics[1]
        change_point_thumbnail(new_latest_picture, context={"request": request})
    elif "viewpoint_picture" in picture.viewpoint.point.properties:
        # just remove the viewpoint_picture from point properties
        picture.viewpoint.point.properties.pop("viewpoint_picture")
        picture.viewpoint.point.save()
