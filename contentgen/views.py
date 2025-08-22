"""Views for content generation blog."""
from django.views.generic import DetailView, ListView

from .models import Article

class ArticleListView(ListView):
    """Public index of published articles."""

    queryset = Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by("-published_at")
    paginate_by = 10
    template_name = "contentgen/article_list.html"

class ArticleDetailView(DetailView):
    """Display a single article."""

    model = Article
    slug_field = "slug"
    template_name = "contentgen/article_detail.html"

class TagFilteredView(ArticleListView):
    """Filter published articles by tag."""

    def get_queryset(self):
        tag = self.kwargs["tag"]
        base = super().get_queryset()
        ids = [a.id for a in base if tag in (a.idea.tags or [])]
        return base.filter(id__in=ids)
