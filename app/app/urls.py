
from django.contrib import admin
from django.urls import path, include
from specialwidget.views import *
from django.contrib.auth import views as auth_views
from specialwidget.help import *


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("", home, name="home"),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),

    # password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    ##dashboard 
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/subscribers", dashboard_subscribers, name="dashboard_subscribers"),
    path("dashboard/support", dashboard_support, name="dashboard_support"),
    path("dashboard/billing", dashboard_billing, name="dashboard_billing"),
    path("dashboard/iframe/<int:id>", widget_iframe, name="dashboard_iframe"),
    path('dashboard/settings/', dashboard_settings, name="dashboard_settings"),
    path('dashboard/integration/', dashboard_integrations, name="dashboard_integrations"),
    path('dashboard/google/', dashboard_google, name="dashboard_google"),

    ###  Google GMB API
    path('gmb', gmb,name='gmb'),

    ####  AJAX CALL URLS
    path('colorpicker/',colorpicker,name="colorpicker"),
    path('a/<int:id>',analytics,name="analytics"),
    path('get_locations_from_google/', search_google, name="get_locations_from_google"),
    path('final_onboarding',final_onboarding,name="final_onboarding"),
    path('add_special/',add_special,name="add_special"),
    path('special_confirm/<int:id>',special_confirm,name="special_confirm"),
    path('edit_special/<int:id>',edit_special,name="edit_special"),
    path('delete_special/<int:id>', delete_special, name="delete_special"),
    path('reactivate_special/<int:id>',reactivate_special,name="reactivate_special"),
    path('deactivate_special/<int:id>',deactivate_special,name="deactivate_special"),
    path('special_analytics/<int:id>',special_analytics,name="special_analytics"),
    path('add_auth_user',add_auth_user,name="add_auth_user"),
    path('add_subscriber/<int:member_id>/<str:email>/<int:special_id>',add_subscriber,name="add_subscriber"),
    #widget html file
    path('specialwidget/widget/',special_widget_html),
    ### Stripe Pages
    path('stripe_webhook/',stripe_webhook,name="stripe_webhook"),
    path('checkout/',checkout,name="checkout"),
    path('inter/',inter,name="inter"),

    path('__debug__/', include('debug_toolbar.urls')),
]
