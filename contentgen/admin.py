"""Admin registrations for content generation models."""
from django.contrib import admin

from .models import Article, ArticleRevision, Idea, SeedDoc

@admin.register(SeedDoc)
class SeedDocAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")

@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ("title", "score", "status", "created_at")
    list_filter = ("status",)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_at")
    list_filter = ("status",)
    prepopulated_fields = {"slug": ("title",)}

@admin.register(ArticleRevision)
class ArticleRevisionAdmin(admin.ModelAdmin):
    list_display = ("article", "step", "created_at")
    list_filter = ("step",)
