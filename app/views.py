from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Special, EmailSignup, SpecialAnalytics, Integration
from .forms import SpecialForm
from .ai import enhance_special_content
from django.db import models
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from profiles.models import UserProfile
import json
import logging
from django.db.models import Q, F
from django.urls import reverse
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
from .integrations import google as google_integration

load_dotenv()  # take environment variables

def dashboard(request):
    """Renders the main dashboard."""
    specials = Special.objects.filter().order_by("-start_date", "-created_at")
    return render(request, "app/dashboard.html", {"specials": specials})



def appertivo_widget(request):
    api_url = "https://appertivo.com/api/specials.js"
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



@login_required
def special_create(request):
    user_profile = request.user.userprofile

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
        return render(request, "app/special_step1.html", {"form": form})

    form = SpecialForm()
    return render(request, "app/special_step1.html", {"form": form})



@login_required(login_url="signup")
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

@login_required
@require_POST
def special_publish(request, pk):
    sp = get_object_or_404(Special, pk=pk)
    sp.published = True
    sp.save(update_fields=["published"])
    integrations = Integration.objects.filter(user_profile=sp.user_profile, enabled=True)
    for integration in integrations:
        if integration.provider == "google":
            google_integration.publish_special(sp)
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
    special_id = data.get("special_id")
    if not email or not restaurant_id:
        return JsonResponse({"success": False}, status=400)

    try:
        profile = UserProfile.objects.get(id=restaurant_id)
    except UserProfile.DoesNotExist:
        return JsonResponse({"success": False}, status=404)

    special = None
    if special_id:
        try:
            special = Special.objects.get(pk=special_id)
        except Special.DoesNotExist:
            special = None

    EmailSignup.objects.create(user_profile=profile, email=email, special=special)
    return JsonResponse({"success": True})


@csrf_exempt
@require_POST
def track_open(request, pk):
    """Record that a special was opened in the widget."""
    sp = get_object_or_404(Special, pk=pk)
    analytics, _ = SpecialAnalytics.objects.get_or_create(special=sp)
    SpecialAnalytics.objects.filter(pk=analytics.pk).update(opens=F("opens") + 1)
    return JsonResponse({"success": True})


@csrf_exempt
@require_POST
def track_cta(request, pk):
    """Record a click on a special's call-to-action."""
    sp = get_object_or_404(Special, pk=pk)
    analytics, _ = SpecialAnalytics.objects.get_or_create(special=sp)
    SpecialAnalytics.objects.filter(pk=analytics.pk).update(cta_clicks=F("cta_clicks") + 1)
    return JsonResponse({"success": True})

# views.py
from django.db.models import Sum, Value, IntegerField
from django.db.models.functions import Coalesce


@login_required
@require_http_methods(["POST"])
def integrations_toggle(request, provider: str):
    """
    HTMX endpoint to enable/disable an integration.
    Expects form or JSON field 'enabled' -> true/false.
    """
    profile = request.user.userprofile
    if not getattr(profile, "is_premium", False):
        return HttpResponseForbidden("Upgrade to premium to access integrations")

    # Accept either form-encoded (hx-vals) or raw JSON
    enabled = None
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8"))
            enabled = payload.get("enabled")
        except Exception:
            return HttpResponseBadRequest("Invalid JSON")
    else:
        # form-encoded
        val = request.POST.get("enabled")
        if val is not None:
            enabled = (str(val).lower() in ("1", "true", "yes", "on"))

    if enabled is None:
        return HttpResponseBadRequest("Missing 'enabled'")
    integration, _ = Integration.objects.get_or_create(
        user_profile=profile, provider=provider
    )
    integration.enabled = enabled
    integration.save(update_fields=["enabled"])

    return JsonResponse({"provider": provider, "enabled": enabled})

@login_required
def integrations_connect(request, provider: str):
    """
    A simple stub page (or start an OAuth flow).
    """
    profile = request.user.userprofile
    if not getattr(profile, "is_premium", False):
        return HttpResponseForbidden("Upgrade to premium to access integrations")

    if provider == "google":
        return redirect(google_integration.get_authorization_url())
    return JsonResponse({"provider": provider, "action": "configure"})

@login_required
def my_specials(request):
    profile = request.user.userprofile

    specials = (Special.objects
                .filter(user_profile=profile)
                .order_by("-created_at"))

    today = timezone.localdate()
    active_special = (specials
                      .filter(published=True)
                      .filter(Q(end_date__gte=today) | Q(end_date__isnull=True))
                      .select_related("analytics")
                      .first())

    # Aggregate across related analytics, defaulting to 0 when none exist
    agg = specials.aggregate(
        opens=Coalesce(Sum("analytics__opens"), Value(0), output_field=IntegerField()),
        cta_clicks=Coalesce(Sum("analytics__cta_clicks"), Value(0), output_field=IntegerField()),
        email_signups=Coalesce(Sum("analytics__email_signups"), Value(0), output_field=IntegerField()),
    )

    subscribers = (EmailSignup.objects
                   .filter(user_profile=profile)
                   .order_by("-created_at"))

    context = {
        "specials": specials.select_related("analytics"),  # fast access in templates
        "active_special": active_special,
        "stats": agg,
        "subscribers": subscribers,
        "integration_status": {i.provider: i.enabled for i in Integration.objects.filter(user_profile=profile)},
    }
    return render(request, "app/my_specials.html", context)


@require_POST
@login_required
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


@login_required
@require_http_methods(["DELETE"])
def special_delete(request, pk):
    profile = request.user.userprofile
    sp = get_object_or_404(Special, pk=pk, user_profile=profile)
    sp.delete()
    return HttpResponse("")
