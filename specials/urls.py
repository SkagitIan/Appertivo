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
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('specials/', views.specials_list, name='specials_list'),
    path('specials/create/', views.create_special, name='create_special'),
    path('connections/', views.connections, name='connections'),
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
