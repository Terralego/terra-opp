TROPP_URL_FETCHER = "terra_opp.renderers.django_url_fetcher"

TROPP_PICTURES_STATES_WORKFLOW = False

TROPP_VIEWPOINT_PROPERTIES_SET = {
    "pdf": {
        ("camera", "Appareil photo"),
    },
    "form": {},
    "filter": {},
}

TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT = ()

TROPP_SEARCHABLE_PROPERTIES = {
    "road": {
        "json_key": "voie",
        "type": "text",
    },
    "site": {
        "json_key": "site",
        "type": "text",
    },
}

# Create a geostore layer and provide its Primary Key here
TROPP_OBSERVATORY_LAYER_PK = None
TROPP_OBSERVATORY_ID = None

TERRA_APPLIANCE_SETTINGS = {}
