from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Special, EmailSignup
from .forms import SpecialForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from profiles.models import UserProfile
from django.db.models import Q
from django.urls import reverse
import json
import logging
from types import SimpleNamespace
logger = logging.getLogger(__name__)


def dashboard(request):
    form = SpecialForm()
    return render(request, 'app/dashboard.html', {'form': form})

def appertivo_widget(request):
    api_url = request.build_absolute_uri("/api/specials.js")
    subscribe_url = request.build_absolute_uri("/api/subscribe/")
    restaurant_id = request.GET.get('restaurant', '')

    response = render(request, "app/widget_template.html", {
        "api_url": api_url,
        "subscribe_url": subscribe_url,
        "restaurant_id": restaurant_id,
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
    # 1) Get param; optionally fall back to a configured demo restaurant
    requested_restaurant = request.GET.get("restaurant",13)
    demo_mode = False
    restaurant_id = requested_restaurant

    # 2) If still no id at all, return static demo payload (safe & fast)
    if not restaurant_id:
        return JsonResponse({
            "specials": DEMO_SPECIALS,
            "meta": {"mode": "default_demo", "restaurant": None, "count": len(DEMO_SPECIALS)}
        })
    print("Restaurant ID:", restaurant_id)
    # 3) Query current, published specials for that restaurant
    qs = (Special.objects
          .filter(
              Q(user_profile__pk=restaurant_id),
              Q(published=True),
              Q(start_date__lte=today) | Q(start_date__isnull=True),
              Q(end_date__gte=today) | Q(end_date__isnull=True),
          ))

    latest = qs.last()

    if demo_mode:
        return JsonResponse({
            "specials": DEMO_SPECIALS,
            "meta": {
                "mode": "default_demo",
                "restaurant": None,
                "count": len(DEMO_SPECIALS),
                "note": "No active specials for demo restaurant; using static demo."
            }
        })
    # 5) Passthrough payload (you’re storing Cloudinary + URLs already)
    payload = {
        "title": latest.title or "",
        "description": latest.description or "",
        "image_url": latest.image or "",            # URLField → Cloudinary URL as-is
        "order_url": latest.order_url or "",
        "phone_number": latest.phone_number or "",
        "mobile_order_url": latest.mobile_order_url or "",
        "cta_choices": latest.cta_choices,          # whatever type you store
        "enable_email_signup": bool(latest.enable_email_signup),
        "start_date": latest.start_date,
        "end_date": latest.end_date,
        "published": bool(latest.published),
    }

    return JsonResponse({
        "specials": [payload],
        "meta": {
            "mode": "demo_restaurant" if demo_mode else "live",
            "restaurant": restaurant_id,
            "count": 1,
        }
    })



def special_create(request):
    """Create a draft special then redirect to preview."""
    if request.method == 'POST':
        form = SpecialForm(request.POST, request.FILES)
        if form.is_valid():
            special = form.save(commit=False)
            special.user_profile = getattr(request, 'user_profile', None)
            special.published = False
            special.save()
            return redirect('special_preview', pk=special.pk)
    else:
        form = SpecialForm()
    return render(request, 'app/dashboard.html', {'form': form})


def _build_preview(special):
    ctas = []
    for choice in special.cta_choices:
        if choice == 'order' and special.order_url:
            ctas.append({'type': 'order', 'url': special.order_url})
        elif choice == 'call' and special.phone_number:
            ctas.append({'type': 'call', 'phone': special.phone_number})
        elif choice == 'mobile_order' and special.mobile_order_url:
            ctas.append({'type': 'mobile_order', 'url': special.mobile_order_url})
    return SimpleNamespace(title=special.title, description=special.description, image=special.image, cta=ctas, enable_email_signup=special.enable_email_signup)


def special_preview(request, pk):
    special = get_object_or_404(Special, pk=pk)
    if request.method == 'POST':
        form = SpecialForm(request.POST, request.FILES, instance=special)
        if form.is_valid():
            special = form.save(commit=False)
            special.user_profile = getattr(request, 'user_profile', None) or special.user_profile
            special.published = False
            special.save()
            form = SpecialForm(instance=special)
    else:
        form = SpecialForm(instance=special)
    preview = _build_preview(special)
    context = {'form': form, 'special': special, 'preview_special': preview, 'form_action': reverse('special_preview', args=[special.pk])}
    return render(request, 'app/special_preview.html', context)


@require_POST
def special_publish(request, pk):
    special = get_object_or_404(Special, pk=pk)
    special.published = True
    special.save(update_fields=['published'])
    return redirect('my_specials')


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
        return redirect("dashboard")

    specials = Special.objects.filter(user_profile=profile).order_by('-created_at')
    return render(request, "app/my_specials.html", {"specials": specials})

