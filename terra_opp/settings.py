from django.conf import settings
from terra_utils.helpers import Choices

STATES = getattr(settings, 'TROPP_STATES', Choices(
    ('DRAFT', 100, 'Draft'),
    ('SUBMITTED', 200, 'Submitted'),
    ('ACCEPTED', 300, 'Accepted'),
    ('REFUSED', -1, 'Refused'),
    ('CANCELLED', -100, 'Cancelled'),
    ('MISSING', 0, 'Missing'),
))

BASE_LAYER_NAME = getattr(settings, 'TROPP_BASE_LAYER_NAME', 'Base opp layer')

PICTURES_STATES_WORKFLOW = getattr(settings, 'TROPP_PICTURES_STATES_WORKFLOW', False)

VIEWPOINT_PROPERTIES_SET = getattr(settings, 'TROPP_VIEWPOINT_PROPERTIES_SET', {
    'pdf': {
        ('camera', 'Appareil photo'),
    },
    'form': {},
    'filter': {},
})

FEATURES_PROPERTIES_FROM_VIEWPOINT = getattr(settings, 'TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT', [
    'commune',
])

SEARCHABLE_PROPERTIES = getattr(settings, 'TROPP_SEARCHABLE_PROPERTIES', {
    'cities': {
        'json_key': 'commune',
        'type': 'single',
    },
    'themes': {
        'json_key': 'themes',
        'type': 'many',
    },
    'road': {
        'json_key': 'voie',
        'type': 'text',
    },
    'site': {
        'json_key': 'site',
        'type': 'text',
    },
})
