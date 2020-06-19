from django import template
from versatileimagefield.files import VersatileImageFieldFile
from versatileimagefield.utils import get_url_from_image_key

register = template.Library()


@register.filter
def as_versatile(file, image_key):
    """
    :param file: a FileField value
    :param image_key: a versatile image key
    :return: a sized image url for a normal file

    Example: {{ instance.document|as_versatile:'thumbnail__750x1500' }}
    """
    file.field.ppoi_field = None  # hack to make this work
    versatile_file = VersatileImageFieldFile(file, file.field, file.name)
    return get_url_from_image_key(versatile_file, image_key)
