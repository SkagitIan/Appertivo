from django.contrib import admin
from specialwidget.models import *

# Register your models here.
@admin.register(Special)
class SpecialAdmin(admin.ModelAdmin):
    list_display = ('title','price','image','active','membership','view')

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    pass

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    pass

@admin.register(GMBAccounts)
class GMBAccountsAdmin(admin.ModelAdmin):
    pass

@admin.register(GMBLocations)
class GMBLocationsAdmin(admin.ModelAdmin):
    pass

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    pass

