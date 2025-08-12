from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = reverse('verify_email', args=[uid, token])
    message = render_to_string('emails/verify_email.html', {
        'user': user,
        'verification_link': link,
    })
    send_mail('Verify your email', message, settings.DEFAULT_FROM_EMAIL, [user.email])
