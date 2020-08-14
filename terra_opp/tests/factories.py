import factory
from django.utils import timezone
from factory.django import FileField

from terra_opp.models import Campaign, Picture, Viewpoint


class CampaignFactory(factory.django.DjangoModelFactory):
    owner = factory.SubFactory(
        'terra_accounts.tests.factories.TerraUserFactory'
    )
    assignee = factory.SubFactory(
        'terra_accounts.tests.factories.TerraUserFactory'
    )

    class Meta:
        model = Campaign


class ViewpointFactory(factory.django.DjangoModelFactory):
    point = factory.SubFactory(
        'geostore.tests.factories.FeatureFactory'
    )
    pictures = factory.RelatedFactory(
        'terra_opp.tests.factories.PictureFactory', 'viewpoint'
    )

    class Meta:
        model = Viewpoint


class PictureFactory(factory.django.DjangoModelFactory):
    owner = factory.SubFactory(
        'terra_accounts.tests.factories.TerraUserFactory'
    )
    date = timezone.datetime(2018, 1, 1, tzinfo=timezone.utc)
    file = FileField(from_path='terra_opp/tests/placeholder.jpg')

    class Meta:
        model = Picture
