from terra_utils.helpers import Choices

TROPP_STATES = Choices(
    ('DRAFT', 100, 'Draft'),
    ('SUBMITTED', 200, 'Submitted'),
    ('ACCEPTED', 300, 'Accepted'),
    ('REFUSED', -1, 'Refused'),
    ('CANCELLED', -100, 'Cancelled'),
    ('MISSING', 0, 'Missing'),
)

TROPP_BASE_LAYER_NAME = 'Base opp layer'

TROPP_PICTURES_STATES_WORKFLOW = False

TROPP_VIEWPOINT_PROPERTIES_SET = {
    'pdf': {
        ('camera', 'Appareil photo'),
    },
    'form': {},
    'filter': {},
}

TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT = ("commune",)

TROPP_SEARCHABLE_PROPERTIES = {
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
}
