import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

logger = logging.getLogger(__name__)  # use module-level logger


def send_verification_email(user):
    logger.info("Preparing verification email for user %s", user.email)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse('verify_email', args=[uid, token])  # "/accounts/verify/..."
    absolute_url = f"https://appertivo.com{path}"  # Ensure SITE_URL is set in settings
    message_html = render_to_string('emails/verify_email.html', {
        'user': user,
        'verification_link': absolute_url,
    })


    try:
        sent = send_mail(
            subject="Verify your email",
            message="Please verify your account.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=message_html,   # use HTML template
        )
        logger.info("Verification email sent to %s, result=%s", user.email, sent)
    except Exception as e:
        logger.error("Failed to send verification email to %s: %s", user.email, str(e))
