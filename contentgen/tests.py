"""Tests for the content generation app."""
from django.test import TestCase
from django.urls import reverse

from .models import Article, ArticleRevision, Idea, SeedDoc


class ContentGenModelTests(TestCase):
    """Ensure models can be created and related."""

    def test_create_models(self):
        seed = SeedDoc.objects.create(name="Doc", text="text")
        idea = Idea.objects.create(title="Idea", angle="Angle")
        article = Article.objects.create(title="Article", slug="article-slug", idea=idea)
        ArticleRevision.objects.create(article=article, step="draft", content_md="content")

        self.assertEqual(seed.name, "Doc")
        self.assertEqual(article.slug, "article-slug")
        self.assertEqual(article.revisions.count(), 1)


class BlogViewTests(TestCase):
    """Verify basic blog views work."""

    def setUp(self):
        idea = Idea.objects.create(title="Idea", angle="Angle", tags=["tag1"])
        self.article = Article.objects.create(
            title="Article", slug="article", status=Article.STATUS_PUBLISHED, idea=idea
        )
        ArticleRevision.objects.create(article=self.article, step="draft", content_md="c")

    def test_article_list_view(self):
        response = self.client.get(reverse("contentgen:article_list"))
        self.assertContains(response, self.article.title)

    def test_article_detail_view(self):
        response = self.client.get(reverse("contentgen:article_detail", args=[self.article.slug]))
        self.assertContains(response, self.article.title)

    def test_tag_filter_view(self):
        response = self.client.get(reverse("contentgen:article_by_tag", args=["tag1"]))
        self.assertContains(response, self.article.title)
