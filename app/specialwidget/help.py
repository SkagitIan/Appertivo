from django.shortcuts import render, redirect
from django.urls import reverse
import requests
import os
import json
import stripe
from specialwidget.forms import AddSpecialForm, SignUpForm
from specialwidget.models import Payment, Membership, Special,Subscriber,GMBAccounts,GMBLocations
from datetime import datetime
from django.http import HttpResponse, JsonResponse,HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import never_cache
import cloudinary
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from urllib.parse import unquote
from requests.exceptions import HTTPError
from specialwidget.tasks import postSpecialtoGoogle, getImageURLS


def colorpicker(request):
    if request.method == "GET":
        membership = Membership.objects.get(user=request.user)
        membership.color = request.GET.get('color')
        membership.save()
        messages.success(request,'Color Updated')
        return render (request, 'ajax/color.html', {'color':request.GET.get('color')})

def add_auth_user(request):
    if request.method == "GET":
        form = SignUpForm()
        return render(request,'specialwidget/special_form.html', {'form':form})
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            f = form.save()
            membership = Membership.objects.get(id=request.POST.get('member_id'))
            membership.user.add(f)
            print(membership)
            messages.success(request,'User Added!')
            return redirect('dashboard_settings')
        else:
            print(form.errors)
            messages.success(request,form.errors)
        return redirect('dashboard_settings')

def add_subscriber(request,member_id,special_id,email, *args,**kwargs):
    if request.method == 'GET':
        membership = Membership.objects.get(id=member_id)
        special = Special.objects.get(id=special_id)
        new_sub = Subscriber(membership=membership,special=special,email=email)
        new_sub.save()
        print(new_sub)
        data = render(request,'ajax/add_subscriber_confirm.html')
        return HttpResponse(data)

def get_cloudinary_image(image):
    image = cloudinary.api.resource(image,cloud_name='dfz4bhlzs',api_key='258173152359737',api_secret="rNOhGbPWTjdXof0aKs656ThFLNc")
    return image['url']

def edit_special(request,id):
    special = Special.objects.get(id=id)
    form = AddSpecialForm(instance=special)
    return render(request,'ajax/edit_special_form.html', {'form':form,'special':special})

@csrf_exempt
def delete_special(request,id):
    if request.method == "DELETE":
        special = Special.objects.get(id=id).delete()
        messages.success(request,'Special is Deleted!')
        response = HttpResponse()
        response["HX-Redirect"] = reverse('dashboard')
        return response 

def deactivate_special(request,id):
    if request.method == "GET":
        special = Special.objects.get(id=id)
        special.active = False
        special.save()
        messages.success(request,'Special is Inactive!')
        response = HttpResponse()
        response["HX-Redirect"] = reverse('dashboard')
        return response 

def reactivate_special(request,id):
    if request.method == "GET":
        special = Special.objects.get(id=id)
        special.active = True
        special.save()
        messages.success(request,'Special is Live!')
        response = HttpResponse()
        response["HX-Redirect"] = reverse('dashboard')
        return response 

def special_analytics (request,id):
    pass

def add_special(request):
    if request.method == "POST":
        form = AddSpecialForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            data = form.instance
            print(data)
            getImageURLS.delay(data) ### GET Social media size image urls
            ####  Send to GMB
            membership = Membership.objects.get(user=request.user)
            
            return render(request, 'ajax/add_special_confirm.html', {'data':data} )
        else:
            data = form.errors
            print(data)
            messages.error(request, form.errors)
            return render(request, 'ajax/add_special_confirm.html', {'data':data} )
    if request.method == "GET":
            membership = Membership.objects.get(user=request.user)
            form = AddSpecialForm(initial={'membership':membership})
            return render(request, 'ajax/special_form.html',{'form':form})

def special_confirm(request,id):
    special = Special.objects.get(id=id)
    special.active = True
    special.save()
    postSpecialtoGoogle.delay(request=request,member=special.membership,special=special)
    messages.success(request,'Special is Live!')
    response = HttpResponse()
    response["HX-Redirect"] = reverse('dashboard')
    return response 

def final_onboarding(request):
    if request.method == "GET":
        
        return render(request, 'onboarding/step3.html')
    
    if request.method == "POST":
        new_member = request.session.get('new_membership')
        new_membership = Membership(
                                date_added = datetime.today(),
                                business_name = new_member['name'],
                                address = new_member['street'],
                                city = new_member['city'],
                                state = new_member['state'],
                                place_id = new_member['place_id'],
                                redirect_url = request.POST.get('url'))
                            
        new_membership.save()
        new_membership.user.add(request.user)   

        print(new_membership)
        del request.session['new_membership']
        response = HttpResponse()
        response["HX-Redirect"] = reverse('dashboard')
        return response

def search_google(request):
    print('search google')  
    data = get_locations_from_google(request,request.GET.get('location'))
    print(f'data from form {data}')
    return render(request, 'onboarding/step2.html',{'data':data})

def get_locations_from_google(request,location):
    ## First search for the place
    key = "AIzaSyAyTp_IugXTvbY0VNafBTbJ6-8ZofLZBlw"
    location = location
    find_place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input="+location+"&inputtype=textquery&key="+key

    request.session['new_membership'] = {}

    response = requests.get(find_place_url, headers={}, data={}).json()
    new_membership = {}
    place_id = response['candidates'][0]['place_id']
    new_membership['place_id'] = place_id
    # ## get more place details from google api
    place_details_url = f"https://maps.googleapis.com/maps/api/place/details/json?key={key}&place_id={place_id}"
    response = requests.get(place_details_url, headers={}, data={}).json()
    for addy in response['result']['address_components']:

        if "subpremise" in addy['types']:
            unit_number = "#"+addy['long_name']
        else:
            unit_number = ""
        if "street_number" in addy['types']:
            street_number = addy['long_name']
        if "route" in addy['types']:
            street = addy['long_name']
            new_membership['street'] = street_number+" "+street+" "+unit_number
        if "locality" in addy['types']:
            new_membership['city'] = addy['long_name']
        if "administrative_area_level_1" in addy['types']:
            new_membership['state'] = addy['short_name']
        if "postal_code" in addy['types']:
            new_membership['zip'] = addy['long_name']
    new_membership['name'] = response['result']['name']
    request.session['new_membership'] = new_membership

    return (new_membership)

def analytics(request,id):
    special = Special.objects.get(id=id)
    special.view += 1
    special.save()
    return JsonResponse ({'views':special.view})

@csrf_exempt
def gmb(request,*args,**kwargs):
    ## HTMX Final Step record name
    if request.method == "POST" and "location_id" in request.POST:
        member = Membership.objects.get(user=request.user)
        member.gmb_location_name = request.POST.get('location_id')
        member.save()
        return render(request, 'gmb/complete.html')
    ## HTMX Locations
    if request.method == "POST" and "account_id" in request.POST:
        print('yes')
        member = Membership.objects.get(user=request.user)
        member.gmb_account_name = request.POST.get('account_id')
        member.save()
        locations = getGMBLocations(request,member.id,request.POST.get('account_id'))
        return render(request, 'gmb/locations.html',{'locations':locations})

    if request.method == "GET" and "code" in request.GET:
        refresh_token = getGMBToken(request.GET.get('code'))
        member = Membership.objects.get(user=request.user)
        member.gmb_refresh_token = refresh_token
        member.gmb_account_list = getGMBAccounts(member)
        member.save()
        print('saved member')
        form = AddSpecialForm(initial={'membership':member})
        return render(request, 'specialwidget/dashboard.html',{'form':form,'member':member})

def getGMBLocations(request,id,account):
    try:
        member = Membership.objects.get(id=id)
        h = {"client_id": os.environ['GOOGLE_CLIENT_ID'],
                    "client_secret":os.environ['GOOGLE_CLIENT_SECRET'],}
        readMask="name,title"
        get_locations_url = "https://mybusinessaccountmanagement.googleapis.com/v1/"+account+"/locations"
        locations = requests.get(get_locations_url,headers=h,params={"readMask":readMask,"access_token":refreshGoogleAccessToken(member.id)}).json()
        for l in locations['locations']:
            n = GMBLocations(membership=member,name=l['name'],title=l['title'])
            n.save()
    except HTTPError as e:
        print(e.response.text)
    return render(request,'gmb/final.html',{'locations':locations})

def getGMBToken(code):
        data = {'grant_type':'authorization_code',
                'code':unquote(code),
                'client_secret':os.environ['GOOGLE_CLIENT_SECRET'],
                'client_id':os.environ['GOOGLE_CLIENT_ID'],
                'redirect_uri':'http://127.0.0.1:8000/gmb'}
        token = requests.post('https://accounts.google.com/o/oauth2/token',json=data, params={'access_type':'offline'}).json()
        print(token['refresh_token'])
        return token['refresh_token']
        
def getGMBAccounts(member):
    h = {"client_id":os.environ['GOOGLE_CLIENT_ID'],
          "client_secret":os.environ['GOOGLE_CLIENT_SECRET'],}
    try:
        get_accounts_url = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts/"
        response = requests.get(get_accounts_url,headers=h,params={"access_token":refreshGoogleAccessToken(member.id)}).json()
    except HTTPError as e:
        print(e.response.text)
    for acc in response['accounts']:
        n = GMBAccounts(membership=member,name=acc['name'],accountName=acc['accountName'])
        n.save()
    return response['accounts']

def getGMBAuthURI():
    flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json',   
                    scopes=['https://www.googleapis.com/auth/business.manage'],
                    redirect_uri='http://127.0.0.1:8000/gmb',
                    )
    gmb_auth_uri = flow.authorization_url(access_type='offline',prompt='consent')
    return gmb_auth_uri[0]

def refreshGoogleAccessToken(id):
        member = Membership.objects.get(id=id)
        params = {
                "grant_type": "refresh_token",
                "client_id":os.environ['GOOGLE_CLIENT_ID'],
                "client_secret":os.environ['GOOGLE_CLIENT_SECRET'],
                "refresh_token": member.gmb_refresh_token
        }
        authorization_url = "https://oauth2.googleapis.com/token"
        r = requests.post(authorization_url, data=params)
        if r.ok:
                member.gmb_access_token = r.json()['access_token']
                member.save()
                return member.gmb_access_token
 
        else:
                return None

stripe.api_key = "sk_test_51HZi5iBM6tLnqpQntc340T6Kh6AtY6merd4pTvTjHsukFi5MC2dC07zHC4bXZlglJBztsOARPY4FOEIDHyGxQaPb005N41pkpr"
#stripe.api_key = "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"
def inter(request,*args,**kwargs):
    '''
        Just a redirect to begin stripe payment
    '''
    return render(request,'onboarding/step5.html') 

@csrf_exempt
def stripe_webhook(request,*args,**kwargs):
    endpoint_secret = 'whsec_CstqITaS5pfysWLjXidPgFvH1vtbzvSs'
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    print('webhook')
    try:
        event = stripe.Webhook.construct_event(
            payload,sig_header,endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        try: 
            res = stripe.Customer.retrieve(event['data']['object'])
            member = Membership.objects.get(user=request.user)
            new_payment = Payment(membership=member,
                                    user=request.user,
                                    amount_total=res['amount_total'],
                                    stripe_id=res['id'],
                                    payment_status=res['payment_status'])
            new_payment.save()
            print(res)
        except:
            print("Couldn't get stripe customer")
    else:
        pass

    return HttpResponse(status=200)

@csrf_exempt
def checkout(request,*args,**kwargs):
    ''' this sets the session ID before the stripe transaction '''
    session = stripe.checkout.Session.create(
        payment_method_types = ['card'],
        line_items = [{'price':'price_1MYxvXBM6tLnqpQnjt31wUhY',
                        'quantity': 1,
                        }],
        mode = 'subscription',
        success_url = 'https://appertivo.com/dashboard',
        cancel_url = request.build_absolute_uri(reverse('home')),

    )
    data = {'session_id' : session.id,
            'stripe_public_key':'pk_live_51HZi5iBM6tLnqpQnM2YDn3aIUOKD6rDUYDNk6UvVm5LZLRkBTv18lHaQUsJvMZGva6bgoCwW6AomSgjdkexKWkhH00SJZGbCb1'}
    return JsonResponse(data)

@csrf_exempt
def fb_getaccess(request,*args,**kwargs):
    user = request.user.id
    user = User.objects.get(id=user)
    code = request.GET.get('code')

    ## translate code to access token
    access_token = requests.get(f'https://graph.facebook.com/v8.0/oauth/access_token?client_id={app_id}&\
        redirect_uri=http://127.0.0.1:8000/fb_getaccess&client_secret={app_secret}&code={code}')
    ## turn access token into long lived access token
    access_code = requests.get(f'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&\
                        client_id={app_id}&client_secret={app_secret}&fb_exchange_token={access_token}"')
    
    savecode = Membership.objects.get(user=user)
    savecode.access_code = access_code
    savecode.save()
    return render(request,'specials/home.html')