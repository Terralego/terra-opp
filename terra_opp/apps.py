from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class TerraOppConfig(AppConfig):
    name = 'terra_opp'

    def ready(self):
        import terra_opp.signals  # noqa
        if 'versatileimagefield' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                f"'{self.name}' needs 'versatileimagefield' in INSTALLED_APPS"
            )

        from . import settings as defaults
        dj_settings = settings._wrapped.__dict__
        for name in dir(defaults):
            dj_settings.setdefault(name, getattr(defaults, name))
