"""Tests for article system."""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Article, publish_article_from_json


class ArticleTests(TestCase):
    """Tests for listing and displaying articles."""

    def setUp(self):
        self.article = Article.objects.create(
            title="Test Article",
            description="Short description",
            content="Full content",
            published_at=timezone.now(),
        )

    def test_resources_page_lists_articles(self):
        response = self.client.get(reverse("resources"))
        self.assertContains(response, self.article.title)

    def test_article_detail_page(self):
        response = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.article.content)

    def test_publish_article_from_json(self):
        data = {
            "title": "JSON Article",
            "description": "Desc",
            "content": "Body",
            "tags": ["seo", "django"],
        }
        article = publish_article_from_json(data)
        self.assertEqual(article.title, "JSON Article")
        self.assertEqual(article.tags, "seo,django")

