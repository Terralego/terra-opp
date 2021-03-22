from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from pathlib import Path

try:
    from django.db.models import JSONField
except ImportError:  # TODO Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField

from django.utils.translation import ugettext_lazy as _
from versatileimagefield.fields import VersatileImageField

from terra_settings.mixins import BaseUpdatableModel
from geostore.models import Feature

# from django.db.models import Count


class BaseLabelModel(BaseUpdatableModel):
    label = models.CharField(_("Label"), max_length=100)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.label}"


class ViewpointsManager(models.Manager):
    def with_accepted_pictures(self):
        return (
            super()
            .get_queryset()
            .filter(
                pictures__state="accepted",
            )
            .distinct()
        )


class City(BaseLabelModel):
    class Meta:
        verbose_name_plural = _("Cities")


class Theme(BaseLabelModel):
    pass


class Viewpoint(BaseLabelModel):
    point = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name="points",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="viewpoints",
        null=True,
    )
    themes = models.ManyToManyField(
        Theme,
        related_name="viewpoints",
    )
    properties = JSONField(_("Properties"), default=dict, blank=True)
    related = GenericRelation("datastore.RelatedDocument")
    active = models.BooleanField(_("Active"), default=True)

    objects = ViewpointsManager()

    @property
    def ordered_pics(self):
        if hasattr(self, "_ordered_pics"):
            # if _ordered_pics set by prefetch on qs, get it
            return self._ordered_pics
        else:
            # not prefetch, compute
            return self.pictures.order_by("-created_at")

    @property
    def ordered_pics_by_date(self):
        return self.pictures.order_by("date")

    @property
    def picture(self):
        pics = self.ordered_pics
        return pics[0].file if pics else None

    class Meta:
        permissions = (("can_download_pdf", "Is able to download a pdf document"),)
        ordering = ["-created_at"]


class Campaign(BaseLabelModel):
    STATES = (
        ("draft", _("Draft")),
        ("started", _("Started")),
        ("closed", _("Closed")),
    )

    start_date = models.DateField(_("Start date"))
    viewpoints = models.ManyToManyField(
        Viewpoint,
        related_name="campaigns",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_("Owner"),
        related_name="campaigns",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_("Assigned to"),
        related_name="assigned_campaigns",
    )
    state = models.CharField(_("State"), default="draft", max_length=10, choices=STATES)

    @property
    def statistics(self):
        return {"total": self.viewpoints.count()}

        # Kept for later
        """queryset = self.objects.aggregate(total=Count("viewpoints")).values("total")

        # TODO add campaign start date filter
        queryset = self.viewpoints.annotate(
            total=models.Count("pk"),
            missing=models.Count(
                "pictures", filter=models.Q(pictures__date__gte=self.start_date)
            ),
            pending=models.Count(
                "pictures",
                filter=models.Q(
                    pictures__state=settings.TROPP_STATES.DRAFT,
                    pictures__date__gte=self.start_date,
                ),
            ),
            accepted=models.Count(
                "pictures",
                filter=models.Q(
                    pictures__state=settings.TROPP_STATES.ACCEPTED,
                    pictures__date__gte=self.start_date,
                ),
            ),
        ).values("total", "missing", "pending", "accepted")
        try:
            return queryset[0]
        except IndexError:
            return {"total": 0, "missing": 0, "accepted": 0, "pending": 0}"""

    @property
    def status(self):
        # TODO Handle missing photo
        return not self.viewpoints.exclude(
            pictures__state="accepted",
        ).exists()

    class Meta:
        ordering = ["-start_date", "-created_at"]


def image_upload_to(instance, filename):
    date_str = instance.date.strftime("%Y-%m-%d_%H-%M-%S")
    filename = Path(filename)
    return f"pictures/viewpoint_{instance.viewpoint.id}/{date_str}{filename.suffix}"


class Picture(BaseUpdatableModel):
    STATES = (
        ("draft", _("Draft")),
        ("submited", _("Submited")),
        ("accepted", _("Accepted")),
        ("refused", _("Refused")),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_("Owner"),
        related_name="pictures",
    )
    viewpoint = models.ForeignKey(
        Viewpoint,
        on_delete=models.CASCADE,
        related_name="pictures",
    )
    # States may be : draft, submitted, accepted, refused
    state = models.CharField(_("State"), default="draft", choices=STATES, max_length=10)

    properties = JSONField(_("Properties"), default=dict, blank=True)
    file = VersatileImageField(_("File"), upload_to=image_upload_to)

    # Different from created_at which is the upload date
    date = models.DateTimeField(_("Date"))

    class Meta:
        permissions = (
            ("change_state_picture", "Is able to change the picture " "state"),
        )
        # It's our main way of sorting pictures, so it better be indexed
        indexes = [
            models.Index(fields=["viewpoint", "date"]),
        ]
        get_latest_by = "date"
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def identifier(self):
        obs_id = settings.TROPP_OBSERVATORY_ID
        pic_index = list(
            self.viewpoint.ordered_pics_by_date.values_list("id", flat=True)
        ).index(self.id)
        pic_index += 1  # list index start at 0, picture order start at 1
        return int(f"{obs_id}0{self.viewpoint.id:03}{pic_index:02}")
