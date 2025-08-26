from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app import views
from django.contrib.auth import views as auth_views

from app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.home, name='home'),
    path('resources/', views.resources, name='resources'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('specials/', views.specials_list, name='specials_list'),
    path('specials/create/', views.create_special, name='create_special'),
    path('specials/<uuid:special_id>/unpublish/', views.special_unpublish, name='special_unpublish'),
    path('specials/<uuid:special_id>/publish/', views.special_publish, name='special_publish'),
    path('specials/<uuid:special_id>/delete/', views.special_delete, name='special_delete'),
    path('specials/<uuid:special_id>/edit/', views.special_edit, name='special_edit'),
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
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
