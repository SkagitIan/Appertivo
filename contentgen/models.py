"""Models for the content generation app."""
from django.db import models


class SeedDoc(models.Model):
    """Source material used for idea generation."""

    name = models.CharField(max_length=255)
    text = models.TextField()
    embedding = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Idea(models.Model):
    """Candidate article idea."""

    STATUS_NEW = "new"
    STATUS_SCANNED = "scanned"
    STATUS_OUTLINED = "outlined"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_SCANNED, "Scanned"),
        (STATUS_OUTLINED, "Outlined"),
    ]

    title = models.CharField(max_length=255)
    angle = models.TextField(blank=True)
    score = models.FloatField(default=0)
    tags = models.JSONField(default=list, blank=True)
    constraints_applied = models.JSONField(default=list, blank=True)
    sources = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Article(models.Model):
    """Published article displayed on the blog."""

    STATUS_DRAFT = "draft"
    STATUS_FINAL = "final"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_FINAL, "Final"),
        (STATUS_PUBLISHED, "Published"),
    ]

    idea = models.ForeignKey(
        Idea, on_delete=models.SET_NULL, related_name="articles", blank=True, null=True
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class ArticleRevision(models.Model):
    """Iterative draft of an article."""

    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="revisions"
    )
    step = models.CharField(max_length=50)
    content_md = models.TextField()
    summary = models.TextField(blank=True)
    citations = models.JSONField(default=list, blank=True)
    jsonld = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.article.title} - {self.step}"
