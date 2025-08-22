"""URL patterns for the content generation blog."""
from django.urls import path

from .views import ArticleDetailView, ArticleListView, TagFilteredView

app_name = "contentgen"

urlpatterns = [
    path("blog/", ArticleListView.as_view(), name="article_list"),
    path("blog/tag/<str:tag>/", TagFilteredView.as_view(), name="article_by_tag"),
    path("blog/<slug:slug>/", ArticleDetailView.as_view(), name="article_detail"),
]
