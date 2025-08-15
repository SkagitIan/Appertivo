from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db.models import F
from .models import Special, SpecialAnalytics, EmailSignup
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


@receiver(post_save, sender=Special)
def create_analytics(sender, instance, created, **kwargs):
    if created:
        SpecialAnalytics.objects.get_or_create(special=instance)


@receiver(post_save, sender=EmailSignup)
def increment_email_signups(sender, instance, created, **kwargs):
    if created and instance.special_id:
        analytics, _ = SpecialAnalytics.objects.get_or_create(special=instance.special)
        SpecialAnalytics.objects.filter(pk=analytics.pk).update(
            email_signups=F("email_signups") + 1
        )
