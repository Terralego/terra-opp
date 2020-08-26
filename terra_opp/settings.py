from terra_utils.helpers import Choices

TROPP_URL_FETCHER = 'terra_opp.renderers.django_url_fetcher'

TROPP_STATES = Choices(
    ('DRAFT', 100, 'Draft'),
    ('SUBMITTED', 200, 'Submitted'),
    ('ACCEPTED', 300, 'Accepted'),
    ('REFUSED', -1, 'Refused'),
    ('CANCELLED', -100, 'Cancelled'),
    ('MISSING', 0, 'Missing'),
)

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

# Create a geostore layer and provide its Primary Key here
TROPP_OBSERVATORY_LAYER_PK = None
