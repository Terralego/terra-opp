from django.apps import AppConfig
from django.conf import settings
from rest_framework.reverse import reverse


class TerraOppConfig(AppConfig):
    name = 'terra_opp'

    def ready(self):
        from . import checks  # NOQA

        # Set default settings from this app to django.settings if not present
        from . import settings as defaults
        dj_settings = settings._wrapped.__dict__
        for name in dir(defaults):
            dj_settings.setdefault(name, getattr(defaults, name))
        # Update terra appliance settings with default OPP settings
        terra_settings = getattr(settings, 'TERRA_APPLIANCE_SETTINGS', {})
        modules = terra_settings.get('modules', {})
        modules['OPP'] = {
            "viewpoints": reverse('terra_opp:viewpoint-list'),
            "layer_tilejson": reverse('layer-tilejson', args=(settings.TROPP_OBSERVATORY_LAYER_PK, )),
            "searchable_properties": settings.TROPP_SEARCHABLE_PROPERTIES
        }
        terra_settings.update({'modules': modules})
        # TODO : deprecate setdefault below when frontend is ok with new key in modules OPP
        terra_settings.setdefault(
            'terraOppSearchableProperties',
            settings.TROPP_SEARCHABLE_PROPERTIES
        )
        setattr(settings, 'TERRA_APPLIANCE_SETTINGS', terra_settings)
