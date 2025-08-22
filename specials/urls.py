from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app import views
from profiles import views as profiles_views
from django.contrib.auth import views as auth_views
from allauth.account.views import LogoutView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("specials/create/", views.special_create, name="special_create"),
    path("specials/<int:pk>/preview/", views.special_preview, name="special_preview"),
    # urls.py
    path("specials/<int:pk>/update/", views.special_update, name="special_update"),
    path("specials/<int:pk>/delete/", views.special_delete, name="special_delete"),
    path("specials/<int:pk>/publish/", views.special_publish, name="special_publish"),
    
    path("api/specials.js", views.specials_api, name="specials_api"),
    path("appertivo-widget.js", views.appertivo_widget, name="appertivo_widget"),
    path("api/subscribe/", views.subscribe_email, name="subscribe_email"),
    path("api/specials/<int:pk>/open/", views.track_open, name="track_open"),
    path("api/specials/<int:pk>/cta/", views.track_cta, name="track_cta"),
    #path('api/create-profile/', profiles_views.create_or_update_profile, name='create_or_update_profile'),
    #path("create-profile/", profiles_views.create_or_update_profile, name="create_profile"),

    path("integrations/<slug:provider>/toggle/", views.integrations_toggle, name="integrations_toggle"),
    path("integrations/<slug:provider>/connect/", views.integrations_connect, name="integrations_connect"),

    path("accounts/login/", profiles_views.EmailLoginView.as_view(), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("appertivo/signup/", profiles_views.signup, name="signup"),
    path("accounts/verify/<uidb64>/<token>/", profiles_views.verify_email, name="verify_email"),
    path("activate/<uidb64>/<token>/", profiles_views.activate, name="activate"),
    path("accounts/password_reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), name="password_reset"),
    path("accounts/password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("accounts/reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
    path("accounts/", include("allauth.urls")),
    path("profile/<int:profile_id>/card/", profiles_views.profile_card, name="profile_card"),
    path("profile/<int:profile_id>/edit/", profiles_views.profile_edit, name="profile_edit"),
    path("profile/<int:profile_id>/save/", profiles_views.profile_save, name="profile_save"),

    path("dash/<int:profile_id>/stats/", views.stats_widget, name="stats_widget"),
    path("dash/<int:profile_id>/stats/fragment/", views.stats_fragment, name="stats_fragment"),

    path("subscribers/<int:profile_id>/", views.subscribers_panel, name="subscribers_panel"),
    path("subscribers/<int:profile_id>/list/", views.subscribers_list, name="subscribers_list"),
    path("subscribers/delete/<int:pk>/", views.subscriber_delete, name="subscriber_delete"),


    path("my-specials/", views.my_specials, name="my_specials"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
