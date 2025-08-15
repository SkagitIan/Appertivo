from django.db import models
from django.utils import timezone
from profiles.models import UserProfile  # Adjust import path if needed

class Special(models.Model):
    user_profile = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='specials',
        help_text="Owner of this special"
    )
    title = models.CharField(max_length=60)
    description = models.TextField(max_length=250, blank=True)
    image = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    published = models.BooleanField(default=False)

    # Store CTAs as a JSON list of strings
    cta_choices = models.JSONField(default=list, blank=True)

    order_url = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    mobile_order_url = models.URLField(blank=True, null=True)
    enable_email_signup = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        """Return True if the special's end date has passed."""
        return bool(self.end_date and self.end_date < timezone.now().date())

class EmailSignup(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='email_signups')
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.user_profile}"
