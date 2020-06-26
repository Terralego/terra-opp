from django.core.checks import Warning, Error, register
from django.conf import settings


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
                id='terra_opp.E002',
            )
        )
    return errors


@register()
def check_installed_apps(app_configs, **kwargs):
    errors = []
    if 'versatileimagefield' not in settings.INSTALLED_APPS:
        errors.append(Error(
            "'terra-opp' needs 'versatileimagefield' in INSTALLED_APPS",
            obj=None,
            id='terra_opp.E001',
        ))
    return errors
