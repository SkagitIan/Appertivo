from django.shortcuts import render, redirect
from .forms import AddSpecialForm
from django.contrib.auth.decorators import login_required
from specialwidget.models import Special, Membership, Subscriber,GMBAccounts,GMBLocations,Payment
from specialwidget.help import get_cloudinary_image, getGMBAuthURI
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from datetime import datetime
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import never_cache
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.db.models import Count
from django.shortcuts import get_object_or_404
from google_auth_oauthlib.flow import InstalledAppFlow
from allauth.account.forms import ChangePasswordForm, SignupForm

# Create your views here.

@never_cache
@xframe_options_exempt
def widget_iframe(request,id,*args,**kwargs):
    '''
    Powers the data in the widget
    '''
    if request.method == 'GET':
        member = Membership.objects.get(id=id)
        try:
            special = Special.objects.filter(membership=member,active=True).select_related('membership').order_by('-id').\
            values('title','expires','id','membership__color','img_url','price','description','membership__id')[0]
        except Exception as e:
            print (e)
            special = None 
    print(special)
    html = render(request,'specialwidget/widget.html', {'data':special})
    return HttpResponse(html)

def special_widget_html(request):
    return render(request, 'specialwidget/widget.html')

def home(request):
    return render(request, 'specialwidget/index.html')

@login_required
def dashboard(request):
    try:
        membership = Membership.objects.get(user=request.user)
        if GMBAccounts.objects.filter(membership=membership).exists():
            accounts = GMBAccounts.objects.filter(membership=membership)
        else:
            accounts = None
        if GMBLocations.objects.filter(membership=membership).exists():
            locations = GMBLocations.objects.filter(membership=membership)
        else:
            locations = None
        form = AddSpecialForm(initial={'membership':membership})
        gmb = getGMBAuthURI()
    except:
        ## Start Onboarding Process
        print('onboardme')
        return render(request, 'onboarding/step1.html')

    try:
        data = Special.objects.filter(membership=membership).select_related('membership').order_by('-id').\
            values('title','expires','id','membership__color','img_url','price','description','membership__id','active','view')    
        for d in data:
            d['subs'] = Subscriber.objects.filter(special_id=d['id']).count()
            print(d)
        active = data.filter(active=True)
        inactive = data.filter(active=False)
        print('100%')
        return render(request, 'specialwidget/dashboard.html',{'locations':locations,'accounts':accounts,'gmb':gmb,'form':form,
                                                                'all_data':data,'membership':membership})      
    except:
        pass
        return render(request, 'specialwidget/dashboard.html',{'google_connect':getGMBAuthURI(),'form':form})
    

@login_required
def dashboard_settings(request):
    form = SignupForm()
    membership = Membership.objects.get(user=request.user)
    return render (request, "specialwidget/settings.html", {'membership':membership,'form':form})


@login_required
def dashboard_subscribers(request):
    membership = Membership.objects.get(user=request.user)
    subs = Subscriber.objects.filter(membership=membership)
    return render (request, "specialwidget/subscribers.html",{'membership':membership,'subs':subs})

def dashboard_integrations(request):
    form = SignupForm()
    membership = Membership.objects.get(user=request.user)
    return render (request, "specialwidget/integrations.html", {'membership':membership,'form':form})

def dashboard_support(request):
    membership = Membership.objects.get(user=request.user)
    return render (request, "specialwidget/support.html", {'membership':membership})

def dashboard_billing(request):
    membership = Membership.objects.get(user=request.user)
    payments = Payment.objects.filter(membership=membership)
    status_check = payments.last()
    if status_check.payment_status == 'paid':
        status = True
    else:
        status = False
    return render (request, "specialwidget/billing.html", {'membership':membership,'payments':payments,'status':status})

def dashboard_google(request):
    gmb = getGMBAuthURI()
    membership = Membership.objects.filter(user=request.user).values()[0]
    try:
        title = GMBLocations.objects.get(name=membership['gmb_location_name'])
        membership['gmb_location'] = title.title
    except:
        pass
    return render (request, "specialwidget/google.html", {'membership':membership,'gmb':gmb})
