from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import RegexValidator
import uuid
import json

class Restaurant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant')
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    cuisine_type = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Special(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]
    
    CTA_CHOICES = [
        ('call', 'Call to Order'),
        ('web', 'Web Order'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='specials')
    title = models.CharField(max_length=255)
    description = models.TextField()
    original_description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='specials/', blank=True, null=True)
    image_public_id = models.CharField(max_length=255, blank=True, null=True)
    google_post_name = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    cta_type = models.CharField(max_length=10, choices=CTA_CHOICES, default='web')
    cta_url = models.URLField(blank=True, null=True)
    cta_phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    email_signups = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']

class Connection(models.Model):
    PLATFORM_CHOICES = [
        ('website', 'Website'),
        ('google_business', 'Google My Business'),
        ('pos', 'POS System'),
        ('delivery', 'Delivery Platform'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    is_connected = models.BooleanField(default=False)
    settings = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.platform}"

    class Meta:
        unique_together = ['user', 'platform']


class Integration(models.Model):
    """Minimal stub model for test compatibility."""
    name = models.CharField(max_length=50)

    class Meta:
        app_label = 'app'

# Extend User model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    restaurant_name = models.CharField(max_length=255)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, blank=True, null=True)
    subscription_tier = models.CharField(
        max_length=20, 
        choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
        default='free'
    )

    def __str__(self):
        return f"{self.user.username} - {self.restaurant_name}"


class Subscription(models.Model):
    """Stores a user's subscription details."""

    PLAN_CHOICES = [('pro', 'Pro'), ('enterprise', 'Enterprise')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    stripe_subscription_id = models.CharField(max_length=100)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    started_at = models.DateTimeField(default=timezone.now)
    canceled_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"


class Transaction(models.Model):
    """Individual subscription transactions."""

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='transactions')
    plan = models.CharField(max_length=20, choices=Subscription.PLAN_CHOICES)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    status = models.CharField(max_length=20)
    occurred_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.subscription.user.username} - {self.amount}"

class EmailSignup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_signups')
    email = models.EmailField()
    special = models.ForeignKey(Special, on_delete=models.SET_NULL, null=True, blank=True, related_name='signups')
    signed_up_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['restaurant', 'email']

    def __str__(self):
        return f"{self.email} - {self.restaurant.username}"


class Article(models.Model):
    """SEO-optimized article for resources section."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(help_text="SEO description")
    content = models.TextField()
    published_at = models.DateTimeField(default=timezone.now)
    tags = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated list of tags"
    )

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("article_detail", args=[self.slug])


def publish_article_from_json(payload):
    """Create and publish an :class:`Article` from a JSON payload."""

    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload

    tags = data.get("tags", [])
    if isinstance(tags, list):
        tags = ",".join(tags)

    article = Article.objects.create(
        title=data["title"],
        description=data.get("description", ""),
        content=data.get("content", ""),
        published_at=data.get("published_at", timezone.now()),
        tags=tags,
    )
    return article
