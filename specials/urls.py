from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app import views
from app.special_draft_views import (
    special_draft_step,
    special_draft_ideas,
    special_draft_select,
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.home, name='home'),
    path('resources/', views.resources, name='resources'),
    path('resources/<slug:slug>/', views.article_detail, name='article_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('menu-suggestions/', views.menu_suggestions, name='menu_suggestions'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('subusers/add/', views.add_subuser, name='add_subuser'),
    path('billing/', views.billing, name='billing'),
    path("billing/subscribe/", views.subscribe, name="subscribe"),
    path("billing/portal/", views.billing_portal, name="billing_portal"),
    path("billing/cancel/", views.cancel_subscription, name="cancel_subscription"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
    path('specials/', views.specials_list, name='specials_list'),
    path('specials/create/', views.create_special, name='create_special'),
    path('specials/<uuid:special_id>/unpublish/', views.special_unpublish, name='special_unpublish'),
    path('specials/<uuid:special_id>/publish/', views.special_publish, name='special_publish'),
    path('specials/<uuid:special_id>/delete/', views.special_delete, name='special_delete'),
    path('specials/<uuid:special_id>/edit/', views.special_edit, name='special_edit'),
    path('specials/partial/create/', views.special_form_partial, name='special_form_create_partial'),
    path('specials/<uuid:special_id>/partial/edit/', views.special_form_partial, name='special_form_edit_partial'),
    path('specials/<uuid:special_id>/partial/card/', views.special_card_partial, name='special_card_partial'),
    path('specials/draft/step/<int:step>/', special_draft_step, name='special_draft_step'),
    path('specials/draft/ideas/', special_draft_ideas, name='special_draft_ideas'),
    path('specials/draft/<int:draft_id>/select/', special_draft_select, name='special_draft_select'),

    path('connections/', views.connections, name='connections'),
    path('connections/google/connect/', views.google_connect, name='google_connect'),
    path('connections/google/callback/', views.google_callback, name='google_callback'),
    path('connections/google/select-location/', views.select_google_location, name='select_google_location'),
    path('api/enhance-description/', views.enhance_description, name='enhance_description'),
    
    # Widget endpoints
    path('widget/<int:user_id>/special/', views.widget_special, name='widget_special'),
    path('widget/<int:user_id>/signup/', views.widget_signup, name='widget_signup'),
    path('widget/<int:user_id>/js/', views.widget_js, name='widget_js'),
    path('widget/', views.widget_setup, name='widget_setup'),
    path('analytics/email/', views.email_analytics, name='email_analytics'),

    # Demo widget endpoints
    path('demo-widget/special/', views.demo_widget, name='demo_widget'),
    path('demo-widget/signup/', views.demo_widget_signup, name='demo_widget_signup'),
    path('demo-widget/js/', views.demo_widget_js, name='demo_widget_js'),
    path(
        "subusers/<int:subuser_id>/reset-password/",
        views.reset_subuser_password,
        name="reset_subuser_password",
    ),
    path(
        "subusers/<int:subuser_id>/delete/",
        views.delete_subuser,   # you'll define this if not already
        name="delete_subuser",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
