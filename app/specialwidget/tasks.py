import string
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
import datetime
from celery import shared_task
from requests.exceptions import HTTPError
import os
from celery import Celery
import cloudinary
# setting the Django settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
app = Celery('tasks',broker='amqps://dutizxrx:PLXUjW-DP4SJPhXEaguh8EmwO_HNC6Eh@woodpecker.rmq.cloudamqp.com/dutizxrx')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Looks up for task modules in Django applications and loads them
app.autodiscover_tasks()

cloudinary.config(
    cloud_name = 'dfz4bhlzs',
    api_key = '258173152359737',
    api_secret = 'rNOhGbPWTjdXof0aKs656ThFLNc')

@shared_task()
def getImageURLS(special):
    special.img_url = cloudinary.CloudinaryImage(str(special.image)).build_url()
    special.gmb_image = cloudinary.CloudinaryImage(str(special.image)).build_url(width=250,crop='fill')
    special.fb_image = cloudinary.CloudinaryImage(str(special.image)).build_url()
    special.tw_image = cloudinary.CloudinaryImage(str(special.image)).build_url()
    special.save()
    return special

@shared_task(bind=True)
def postSpecialtoGoogle(requests,member,special):
    today = datetime.datetime.today()
    body = { 
        "languageCode": "EN",
        "summary": special.description,
        "callToAction": {
                "actionType": "ORDER",
                "url": member.redirect_url
                },
        "event": {
            "title":"Current Specials",
            "schedule":{
                "startDate": {
                            "year": int(today.year),
                            "month":int(today.month),
                            "day": int(today.day)
                            },
                "startTime": {
                            "hours": int(today.hour),
                            "minutes":int(today.minute),
                            "seconds": int(today.second),
                            "nanos": int(today.microsecond)
                            },
                "endDate": {
                    "year": int(special.expires.strftime('%Y')),
                    "month":int(special.expires.strftime('%m')),
                    "day": int(special.expires.strftime('%d'))
                    },
                "endTime": {
                            "hours": 23,
                            "minutes": 59,
                            "seconds": 59,
                            "nanos": 59
                            }}
                            },
        "state": 'LIVE',
        "media": [{

                        "mediaFormat": 'PHOTO',
                        "sourceUrl": special.img_url ,
                        }],
        "topicType":"STANDARD",
        "offer": {
                "couponCode": "Specials",
                "redeemOnlineUrl": member.redirect_url,
                "termsConditions": "Only redemable while valid"
                        }
                }
    h = {'Authorization':"Bearer "+help.refreshGoogleAccessToken(4),
        'X-GOOG-API-FORMAT-VERSION': '2'}
    try:
        local_posts_url = f"https://mybusiness.googleapis.com/v4/{member.gmb_account_name}/{member.gmb_location_name}/localPosts"
        response = requests.post(local_posts_url,headers=h,json=body).json()
        special.gmb_localposts = response['name']
        special.save()
    except HTTPError as e:
        print(e.response.text)

    return response.text

