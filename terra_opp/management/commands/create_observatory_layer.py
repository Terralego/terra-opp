from django.conf import settings
from django.core.management import BaseCommand
from geostore import GeometryTypes
from geostore.models import Layer


class Command(BaseCommand):
    help = "Create a django-geostore point layer to store observatory viewpoints"

    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--name", action="store", help="Name for layer to create."
        )
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Create even if the TROPP_OBSERVATORY_LAYER_PK already set.",
        )

    def handle(self, *args, **options):
        existing_observatory = getattr(settings, "TROPP_OBSERVATORY_LAYER_PK")

        name = options.get("name") or "opp_baselayer"
        force = options.get("force")

        if existing_observatory and not force:
            try:
                Layer.objects.get(pk=existing_observatory)
            except Layer.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"Defined layer with PK {existing_observatory} defined in setting TROPP_OBSERVATORY_LAYER_PK does not exists in database (-f to force createn)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"A layer already exists for this TROPP_OBSERVATORY_LAYER_PK: {existing_observatory} - Do nothing"
                    )
                )
        else:
            if force:
                try:
                    # whether a layer with this id already exists
                    Layer.objects.get(pk=existing_observatory)
                    self.stdout.write(
                        self.style.WARNING(
                            f"A layer already exists for this TROPP_OBSERVATORY_LAYER_PK: {existing_observatory} - Do nothing"
                        )
                    )
                    return
                except Layer.DoesNotExist:
                    pass

            try:
                # whether a layer with this name already exists
                layer = Layer.objects.get(name=name)
                self.stdout.write(
                    self.style.WARNING(
                        f"A layer with pk {layer} already exists for this name: {name} - Can't create new one."
                    )
                )
                return
            except Layer.DoesNotExist:
                pass

            layer = Layer.objects.create(geom_type=GeometryTypes.Point, name=f"{name}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Layer has been created. Please set TROPP_OBSERVATORY_LAYER_PK={layer.pk} in project settings"
                )
            )
