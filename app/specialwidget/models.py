from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from datetime import datetime, timedelta
from colorfield.fields import ColorField
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import cloudinary
# Create your models here.

cloudinary.config(
    cloud_name = 'dfz4bhlzs',
    api_key = '258173152359737',
    api_secret = 'rNOhGbPWTjdXof0aKs656ThFLNc')

class Membership(models.Model):
    user = models.ManyToManyField(User)
    date_added = models.DateTimeField(default=timezone.now())
    send = models.BooleanField(default=True)
    business_name = models.CharField(max_length=100,blank=True, null=True,verbose_name="Business Name")
    address = models.CharField(max_length=100,blank=True, null=True)
    city = models.CharField(max_length=100,blank=True, null=True)
    state = models.CharField(max_length=100,blank=True, null=True)
    redirect_url = models.CharField(max_length=100,blank=True, null=True,help_text="This is where uses will be redirected after a call to action (e.g. Website for online ordering...)")
    phone = models.CharField(max_length=100,blank=True, null=True)
    place_id = models.CharField(max_length=300,blank=True, null=True)

    #### Settings
    color = ColorField(default='#F18805')
   ### Twilio Stuff
    twilio_from_sms = models.CharField(max_length=100,blank=True, null=True)

    ### Google GMB stuff
    # gmb_creds = PickledObjectField()
    gmb_credentials = models.CharField(max_length=12000,blank=True, null=True)
    gmb_access_token = models.CharField(max_length=12000,blank=True, null=True)
    gmb_refresh_token = models.CharField(max_length=12000,blank=True, null=True)
    gmb_account_name = models.CharField(max_length=12000,blank=True, null=True)
    gmb_location_name = models.CharField(max_length=12000,blank=True, null=True)


    def __str__(self):
        return self.business_name

class GMBAccounts(models.Model):
    membership = models.ForeignKey(Membership,on_delete=models.CASCADE,default=4)
    name = models.CharField(max_length=100,blank=True, null=True,)
    accountName = models.CharField(max_length=100,blank=True, null=True)

    def __str__(self):
        return self.accountName

class GMBLocations(models.Model):
    membership = models.ForeignKey(Membership,on_delete=models.CASCADE,default=4)
    name = models.CharField(max_length=100,blank=True, null=True)
    title = models.CharField(max_length=100,blank=True, null=True)

    def __str__(self):
        return self.title

class Special(models.Model):
    membership = models.ForeignKey(Membership,on_delete=models.CASCADE,null=True)
    title = models.CharField(max_length=300)
    description = models.CharField(max_length=300)
    image = CloudinaryField('image')
    img_url = models.CharField(max_length=300,default="")
    price = models.CharField(max_length=300)
    expires = models.DateTimeField(default=datetime.today() + timedelta(days=2))
    active = models.BooleanField(default=False)
    view = models.IntegerField(default=0)
    
    gmb_localposts = models.CharField(max_length=3000)
    gmb_image = models.CharField(max_length=3000,blank=True, null=True)
    fb_image = models.CharField(max_length=3000,blank=True, null=True)
    tw_image = models.CharField(max_length=3000,blank=True, null=True)
    
    def save(self, *args, **kwargs):
        super(Special, self).save(*args, **kwargs)

class Subscriber(models.Model):
    email = models.EmailField(max_length=250)
    membership = models.ForeignKey(Membership,on_delete=models.CASCADE,null=True)
    special = models.ForeignKey(Special,on_delete=models.CASCADE,null=True)
    signup_date = models.DateTimeField(auto_now=True)

class Payment(models.Model):
    membership = models.ForeignKey(Membership,on_delete=models.CASCADE,null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    date = models.DateTimeField(auto_now=True)
    amount_total = models.IntegerField()
    stripe_id = models.CharField(max_length=3000)
    payment_status = models.CharField(max_length=300)

