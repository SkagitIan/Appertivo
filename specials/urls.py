from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app import views
from profiles import views as profiles_views



urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("specials/create/", views.special_create, name="special_create"),
    # urls.py
    path("specials/<int:pk>/edit/", views.special_edit, name="special_edit"),
    path("specials/<int:pk>/inline-update/", views.special_inline_update, name="special_inline_update"),

    path("specials/<int:pk>/publish/", views.special_publish, name="special_publish"),
    path("api/specials.js", views.specials_api, name="specials_api"),
    path("appertivo-widget.js", views.appertivo_widget, name="appertivo_widget"),
    path('api/create-profile/', profiles_views.create_or_update_profile, name='create_or_update_profile'),
    path("create-profile/", profiles_views.create_or_update_profile, name="create_profile"),

    path("my-specials/", views.my_specials, name="my_specials"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
