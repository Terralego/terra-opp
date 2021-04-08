from django.apps import AppConfig
from django.conf import settings
from terra_accounts.permissions_mixins import PermissionRegistrationMixin
from rest_framework.reverse import reverse
from django.utils.translation import gettext_lazy as _
from django.db.utils import ProgrammingError


class TerraOppConfig(PermissionRegistrationMixin, AppConfig):
    name = "terra_opp"

    permissions = (
        ("OPP", "can_manage_viewpoints", _("Can manage viewpoints")),
        ("OPP", "can_manage_pictures", _("Can manage pictures")),
        ("OPP", "can_add_pictures", _("Can add pictures")),
        ("OPP", "can_manage_campaigns", _("Can manage campaign")),
    )

    def ready(self):
        from . import checks, receivers  # NOQA
        from geostore import models

        super().ready()

        # Set default settings from this app to django.settings if not present
        from . import settings as defaults

        dj_settings = settings._wrapped.__dict__
        for name in dir(defaults):
            dj_settings.setdefault(name, getattr(defaults, name))

        try:
            opp_layer = models.Layer.objects.get(id=settings.TROPP_OBSERVATORY_LAYER_PK)
        except models.Layer.DoesNotExist:
            pass
        except ProgrammingError:
            # Db should not be initialized
            pass
        else:
            terra_settings = getattr(settings, "TERRA_APPLIANCE_SETTINGS", {})
            modules = terra_settings.get("modules", {})

            # Update terra appliance settings with default OPP settings
            modules["OPP"] = {
                "viewpoints": reverse("terra_opp:viewpoint-list"),
                "layer_tilejson": reverse("layer-tilejson", args=(opp_layer.pk,)),
                "searchable_properties": settings.TROPP_SEARCHABLE_PROPERTIES,
                "layerId": opp_layer.pk,
                "layerName": opp_layer.name,
            }
            terra_settings.update({"modules": modules})
            setattr(settings, "TERRA_APPLIANCE_SETTINGS", terra_settings)
