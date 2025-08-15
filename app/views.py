from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Special, EmailSignup
from .forms import SpecialForm
from .ai import enhance_special_content
from django.db import models
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseBadRequest, QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from profiles.models import UserProfile
import json
import logging
from django.db.models import Q
from django.urls import reverse
logger = logging.getLogger(__name__)
from dotenv import load_dotenv

load_dotenv()  # take environment variables

def dashboard(request):
    """
    Renders the main dashboard: 
    - full-page list of specials 
    - form is included via HTMX fragment
    """
    specials = Special.objects.order_by("-start_date", "-created_at")
    form     = SpecialForm()
    return render(request, "app/dashboard.html", {
        "specials": specials,
        "form": form,
    })



def appertivo_widget(request):
    api_url = request.build_absolute_uri("/api/specials.js")
    subscribe_url = request.build_absolute_uri("/api/subscribe/")
    restaurant_id = request.GET.get('restaurant', '')
    special_id = request.GET.get('special', '')

    response = render(request, "app/widget_template.html", {
        "api_url": api_url,
        "subscribe_url": subscribe_url,
        "restaurant_id": restaurant_id,
        "special_id": special_id,
    })
    response['Content-Type'] = 'application/javascript'
    return response


DEMO_SPECIALS = [
    {
        "title": "Try Me — Daily Special",
        "description": "This is a demo special from Appertivo. Add a photo and a CTA to see how it looks on your site.",
        "image_url": "",  # leave blank or host a small demo image in /static and use request.build_absolute_uri in view
        "cta_choices": [
            {"type": "order", "url": "https://example.com/order"},
            {"type": "call", "phone": "+1-555-0100"},
        ],
        "enable_email_signup": True,
    }
]

def specials_api(request):
    today = timezone.localdate()
    requested_restaurant = request.GET.get("restaurant", 13)
    special = request.GET.get("special", None)
    demo_mode = False
    restaurant_id = requested_restaurant

    # Fallback to static demo
    if not restaurant_id:
        return JsonResponse({
            "specials": DEMO_SPECIALS,
            "meta": {"mode": "default_demo", "restaurant": None, "count": len(DEMO_SPECIALS)}
        })

    print("Restaurant ID:", restaurant_id)

    # If specific special requested
    if special:
        qs = Special.objects.filter(pk=special)
    else:
        qs = Special.objects.filter(
            Q(user_profile__pk=restaurant_id),
            Q(published=True),
            Q(start_date__lte=today) | Q(start_date__isnull=True),
            Q(end_date__gte=today) | Q(end_date__isnull=True),
        )

    latest = qs.last()

    # No special found
    if not latest:
        return JsonResponse({
            "specials": [],
            "meta": {
                "mode": "fallback_empty_restaurant",
                "restaurant": restaurant_id,
                "count": 0,
            }
        })
    cta = []
    if latest.order_url:
        cta.append({"type": "order", "url": latest.order_url})
    if latest.phone_number:
        cta.append({"type": "call", "phone": latest.phone_number})
    if latest.mobile_order_url:
        cta.append({"type": "mobile_order", "url": latest.mobile_order_url})

    payload = {
        "title": latest.title or "",
        "description": latest.description or "",
        "image_url": latest.image or "",
        "order_url": latest.order_url or "",
        "phone_number": latest.phone_number or "",
        "mobile_order_url": latest.mobile_order_url or "",
        "cta_choices": latest.cta_choices,
        "cta": cta,
        "enable_email_signup": bool(latest.enable_email_signup),
        "start_date": latest.start_date,
        "end_date": latest.end_date,
        "published": bool(latest.published),
    }

    return JsonResponse({
        "specials": [payload],
        "meta": {
            "mode": "live",
            "restaurant": restaurant_id,
            "count": 1,
        }
    })



def special_create(request):
    user_profile = getattr(request, 'user_profile', None)

    if request.method == "POST":
        form = SpecialForm(request.POST, request.FILES)
        if form.is_valid():
            special = form.save(commit=False)
            special.published = False
            special.user_profile = user_profile
            special.save()
            if form.cleaned_data.get("ai_enhance"):
                enhance_special_content(special)
            return redirect("special_preview", pk=special.pk)
        specials = Special.objects.order_by("-start_date", "-created_at")
        return render(request, "app/dashboard.html", {"specials": specials, "form": form})
    return redirect("dashboard")


def special_preview(request, pk):
    sp = get_object_or_404(Special, pk=pk)
    if request.method == "POST":
        form = SpecialForm(request.POST, request.FILES, instance=sp)
        if form.is_valid():
            sp = form.save()
            if form.cleaned_data.get("ai_enhance"):
                enhance_special_content(sp)
            form = SpecialForm(instance=sp)
    else:
        form = SpecialForm(instance=sp)
    ctx = {
        "special": sp,
        "form": form,
        "publish_url": reverse("special_publish", args=[sp.pk]),
    }
    return render(request, "app/special_preview.html", ctx)

@require_POST
def special_publish(request, pk):
    sp = get_object_or_404(Special, pk=pk)
    sp.published = True
    sp.save(update_fields=["published"])
    return redirect("my_specials")

@csrf_exempt
@require_POST
def subscribe_email(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False}, status=400)

    email = data.get("email")
    restaurant_id = data.get("restaurant_id")
    if not email or not restaurant_id:
        return JsonResponse({"success": False}, status=400)

    try:
        profile = UserProfile.objects.get(id=restaurant_id)
    except UserProfile.DoesNotExist:
        return JsonResponse({"success": False}, status=404)

    EmailSignup.objects.create(user_profile=profile, email=email)
    return JsonResponse({"success": True})

def my_specials(request):
    profile = getattr(request, "user_profile", None)
    if not profile:
        return redirect("home")

    specials = Special.objects.filter(user_profile=profile).order_by('-created_at')
    return render(request, "app/my_specials.html", {"specials": specials})

@require_POST
def special_update(request, pk):
    sp = get_object_or_404(Special, pk=pk)
    form = SpecialForm(request.POST, request.FILES, instance=sp)
    if form.is_valid():
        sp = form.save()
        if form.cleaned_data.get("ai_enhance"):
            enhance_special_content(sp)
        ctx = {
            "special": sp,
            "form": SpecialForm(instance=sp),
            "action_url": reverse("special_update", args=[sp.pk]),
            "target_id": "#main",
            "submit_label": "Save Changes",
        }
        return render(request, "app/partials/special_edit_panel.html", ctx)

    # on errors: return the same form partial, configured for update
    return render(
        request,
        "app/partials/special_form.html",
        {
            "form": form,
            "action_url": reverse("special_update", args=[pk]),
            "target_id": "#main",
            "submit_label": "Save Changes",
        },
        status=422,
    )
