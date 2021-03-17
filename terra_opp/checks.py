from django.core.checks import Warning, Error, register
from django.conf import settings
from geostore import models
from django.db.utils import ProgrammingError


@register()
def check_dedicated_layer(app_configs, **kwargs):
    errors = []
    observatory_layer_pk = settings.TROPP_OBSERVATORY_LAYER_PK

    if not observatory_layer_pk:
        errors.append(
            Warning(
                "To correctly use OPP You should create a dedicated layer, set TROPP_OBSERVATORY_LAYER_PK and restart your instance as soon as possible.",
                hint="""
                    Create a dedicated point layer with ./manage.py create_observatory_layer and set
                    TROPP_OBSERVATORY_LAYER_PK with given PK.
                    ex: TROPP_OBSERVATORY_LAYER_PK=4
                    """,
                obj=None,
                id="terra_opp.E002",
            )
        )
    else:
        try:
            models.Layer.objects.get(id=observatory_layer_pk)
        except models.Layer.DoesNotExist:
            errors.append(
                Warning(
                    f"Layer with id={observatory_layer_pk} seems missing. Are you sure you've created a layer with this id?",
                    hint="""
                        Create a dedicated point layer with ./manage.py create_observatory_layer and set
                        TROPP_OBSERVATORY_LAYER_PK with given PK.
                        ex: TROPP_OBSERVATORY_LAYER_PK=4
                        """,
                    obj=None,
                    id="terra_opp.E003",
                )
            )
        except ProgrammingError:
            # Database not initialized ?
            pass
    return errors


@register()
def check_opp_id_defined(app_configs, **kwargs):
    errors = []
    tropp_observatory_id = settings.TROPP_OBSERVATORY_ID
    if not tropp_observatory_id:
        errors.append(
            Warning(
                "To correctly use OPP you should set TROPP_OBSERVATORY_ID and restart your instance as soon as possible.",
                hint="""
                    TROPP_OBSERVATORY_ID is the identifier of your observatory at national level
                    Ex: TROPP_OBSERVATORY_ID = 20
                """,
                obj=None,
                id="terra_opp.E004",
            )
        )
    return errors


@register()
def check_installed_apps(app_configs, **kwargs):
    errors = []
    if "versatileimagefield" not in settings.INSTALLED_APPS:
        errors.append(
            Error(
                "'terra-opp' needs 'versatileimagefield' in INSTALLED_APPS",
                obj=None,
                id="terra_opp.E001",
            )
        )
    return errors
