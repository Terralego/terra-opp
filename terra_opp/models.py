from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
try:
    from django.db.models import JSONField
except ImportError:  # TODO Remove when dropping Django releases < 3.1
    from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy as _
from versatileimagefield.fields import VersatileImageField

from terra_settings.mixins import BaseUpdatableModel
from geostore.models import Feature
from .settings import TROPP_STATES as DEFAULT_TROPP_STATES


class BaseLabelModel(BaseUpdatableModel):
    label = models.CharField(_('Label'), max_length=100)

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class ViewpointsManager(models.Manager):
    def with_accepted_pictures(self):
        return super().get_queryset().filter(
            pictures__state=settings.TROPP_STATES.ACCEPTED,
        ).distinct()


class City(BaseLabelModel):
    class Meta:
        verbose_name_plural = _("Cities")


class Theme(BaseLabelModel):
    pass


class Viewpoint(BaseLabelModel):
    point = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='points',
    )
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='viewpoints',
        null=True,
    )
    themes = models.ManyToManyField(
        Theme,
        related_name='viewpoints',
    )
    properties = JSONField(_('Properties'), default=dict, blank=True)
    related = GenericRelation('datastore.RelatedDocument')

    objects = ViewpointsManager()

    @property
    def status(self):
        """
        Return the status of this viewpoint for a campaign
        :param self:
        :return: string (missing, draft, submitted, accepted)
        """
        # Get only pictures created for the campaign
        picture = self.pictures.latest()
        STATES = settings.TROPP_STATES
        if picture.created_at < self.created_at:
            return STATES.CHOICES_DICT[STATES.MISSING]
        return STATES.CHOICES_DICT[picture.state]

    @property
    def ordered_pics(self):
        if hasattr(self, '_ordered_pics'):
            # if _ordered_pics set by prefetch on qs, get it
            return self._ordered_pics
        else:
            # not prefetch, compute
            return self.pictures.order_by('-created_at')

    @property
    def picture(self):
        pics = self.ordered_pics
        return pics[0].file if pics else None

    class Meta:
        permissions = (
            ('can_download_pdf', 'Is able to download a pdf document'),
        )
        ordering = ['-created_at']


class Campaign(BaseLabelModel):
    viewpoints = models.ManyToManyField(
        Viewpoint,
        related_name='campaigns',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='campaigns',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Assigned to'),
        related_name='assigned_campaigns',
    )

    @property
    def statistics(self):
        queryset = self.viewpoints.annotate(
            missing=models.Count('pk', filter=models.Q(
                pictures__isnull=True
            )),
            pending=models.Count('pictures', filter=models.Q(
                pictures__state=settings.TROPP_STATES.DRAFT
            )),
            refused=models.Count('pictures', filter=models.Q(
                pictures__state=settings.TROPP_STATES.REFUSED
            )),
        ).values('missing', 'pending', 'refused')
        try:
            return queryset[0]
        except IndexError:
            return {'missing': 0, 'pending': 0, 'refused': 0}

    @property
    def status(self):
        return not self.viewpoints.exclude(
            pictures__state=settings.TROPP_STATES.ACCEPTED,
        ).exists()

    class Meta:
        permissions = (
            ('manage_all_campaigns', "Can manage all campaigns"),
        )
        ordering = ['-created_at']


class Picture(BaseUpdatableModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='pictures',
    )
    viewpoint = models.ForeignKey(
        Viewpoint,
        on_delete=models.CASCADE,
        related_name='pictures',
    )
    # States may be : draft, metadata_ok (submitted), accepted, refused
    state = models.IntegerField(
        _('State'),
        default=getattr(settings, 'TROPP_STATES', DEFAULT_TROPP_STATES).DRAFT,
    )

    properties = JSONField(_('Properties'), default=dict, blank=True)
    file = VersatileImageField(_('File'))

    # Different from created_at which is the upload date
    date = models.DateTimeField(_('Date'))

    class Meta:
        permissions = (
            ('change_state_picture', 'Is able to change the picture '
                                     'state'),
        )
        # It's our main way of sorting pictures, so it better be indexed
        indexes = [
            models.Index(fields=['viewpoint', 'date']),
        ]
        get_latest_by = 'date'
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not settings.TROPP_PICTURES_STATES_WORKFLOW:
            self.state = settings.TROPP_STATES.ACCEPTED
        super().save(*args, **kwargs)
