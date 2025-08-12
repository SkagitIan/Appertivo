from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings


def send_special_published_email(special):
    profile = special.user_profile
    if not profile or not profile.email:
        return
    edit_link = reverse('special_update', args=[special.pk])
    message = render_to_string('emails/special_published.html', {
        'special': special,
        'edit_link': edit_link,
    })
    subject = f'Your special "{special.title}" is live'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [profile.email])
