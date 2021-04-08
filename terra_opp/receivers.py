from django.db.models.signals import post_save
from django.dispatch import receiver

from terra_opp.models import Picture


@receiver(post_save, sender=Picture)
def create_picture_identifier(sender, instance, **kwargs):
    if instance.state == sender.ACCEPTED and not instance.identifier:
        instance.identifier = instance.get_identifier()
        instance.save()
