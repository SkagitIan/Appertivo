from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Special
from .emails import send_special_published_email


@receiver(pre_save, sender=Special)
def store_published_state(sender, instance, **kwargs):
    if instance.pk:
        previous = Special.objects.get(pk=instance.pk)
        instance._was_published = previous.published
    else:
        instance._was_published = False


@receiver(post_save, sender=Special)
def send_published_email(sender, instance, created, **kwargs):
    if instance.published and (created or not getattr(instance, '_was_published', False)):
        send_special_published_email(instance)
