from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Special
from .forms import SpecialForm
from django.db import models
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseBadRequest, QueryDict
import logging


logger = logging.getLogger(__name__)


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

from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

def appertivo_widget(request):
    api_url = request.build_absolute_uri("/api/specials.js")
    restaurant_id = request.GET.get('restaurant', '')

    response = render(request, "app/widget_template.html", {
        "api_url": api_url,
        "restaurant_id": restaurant_id,
    })
    response['Content-Type'] = 'application/javascript'
    return response
    
def specials_api(request):
    restaurant_id = request.GET.get('restaurant')
    logger.debug("Restaurant ID: %s", restaurant_id)
    today = timezone.localdate()
    qs = Special.objects.filter(
        Q(published=True),
        Q(start_date__lte=today) | Q(start_date__isnull=True),
        Q(end_date__gte=today) | Q(end_date__isnull=True),
    )
    if restaurant_id:
        qs = qs.filter(user_profile__id=restaurant_id)  # or another filter by user/restaurant

    qs = qs.order_by("start_date")

    data = []
    for sp in qs:
        ctas = []
        if "order" in sp.cta_choices:
            ctas.append({"type": "order", "url": sp.order_url})
        if "call" in sp.cta_choices:
            ctas.append({"type": "call", "phone": sp.phone_number})
        if "mobile_order" in sp.cta_choices:
            ctas.append({"type": "mobile_order", "url": sp.mobile_order_url})

        data.append({
            "title": sp.title,
            "description": sp.description,
            "image_url": request.build_absolute_uri(sp.image.url) if sp.image else "",
            "cta": ctas,
            "enable_email_signup": sp.enable_email_signup,
        })

    return JsonResponse({"specials": data})

from django.views.decorators.http import require_POST
from django.http import HttpResponse

def special_create(request):
    user_profile = getattr(request, 'user_profile', None)
    if request.method == "POST":
        form = SpecialForm(request.POST, request.FILES)
        if form.is_valid():
            special = form.save(commit=False)
            special.published = False  # Not published yet
            special.user_profile = user_profile
            special.save()

            ctas = []
            if "order" in special.cta_choices:
                ctas.append({"type": "order", "url": special.order_url})
            if "call" in special.cta_choices:
                ctas.append({"type": "call", "phone": special.phone_number})
            if "mobile_order" in special.cta_choices:
                ctas.append({"type": "mobile_order", "url": special.mobile_order_url})
            special.cta = ctas

            # After creating the special show a preview that matches the widget
            return render(
                request,
                "app/partials/special_preview.html",
                {"special": special},
            )
    else:
        form = SpecialForm()
    return render(request, "app/partials/special_form.html", {"form": form})

# views.py
def special_edit(request, pk):
    special = get_object_or_404(Special, pk=pk, user_profile=request.user_profile)
    form = SpecialForm(instance=special)

    if request.method == "POST":
        form = SpecialForm(request.POST, request.FILES, instance=special)
        if form.is_valid():
            special = form.save()
            ctas = []
            if "order" in special.cta_choices:
                ctas.append({"type": "order", "url": special.order_url})
            if "call" in special.cta_choices:
                ctas.append({"type": "call", "phone": special.phone_number})
            if "mobile_order" in special.cta_choices:
                ctas.append({"type": "mobile_order", "url": special.mobile_order_url})
            special.cta = ctas
            return render(request, "app/partials/special_preview.html", {"special": special})
    
    return render(request, "app/partials/special_form_edit.html", {"form": form, "special": special})

@require_POST
def special_publish(request, pk):
    special = get_object_or_404(Special, pk=pk)
    special.published = True
    special.save()

    embed_code = f'<script src="http://127.0.0.1:8000/appertivo-widget.js?restaurant={special.user_profile.id}"></script>'

    # Render embed code partial with the snippet
    html = render_to_string("app/partials/embed_code.html", {"embed_code": embed_code})

    return HttpResponse(html)

def my_specials(request):
    profile = getattr(request, "user_profile", None)
    if not profile:
        return redirect("home")

    specials = Special.objects.filter(user=profile).order_by('-created_at')
    return render(request, "app/my_specials.html", {"specials": specials})

from django.http import QueryDict
from .forms import SpecialForm
from .models import Special

@require_http_methods(["POST"])
def special_inline_update(request, pk):
    special = get_object_or_404(Special, pk=pk)
    logger.debug(
        "Inline update for special %s with data: %s", special.pk, request.POST
    )
    logger.debug("POST: %s", request.POST)
    logger.debug("FILES: %s", request.FILES)
    
    if request.method == "POST":
        # Create a mutable copy of POST data
        post_data = request.POST.copy()
        
        # Ensure all required fields are present with current values
        required_fields = {
            'title': special.title,
            'description': special.description,
            'start_date': special.start_date.strftime('%Y-%m-%d') if special.start_date else '',
            'end_date': special.end_date.strftime('%Y-%m-%d') if special.end_date else '',
            'cta_choices': special.cta_choices or 'order',
        }
        
        # Add current CTA field values
        if hasattr(special, 'order_url') and special.order_url:
            required_fields['order_url'] = special.order_url
        if hasattr(special, 'phone_number') and special.phone_number:
            required_fields['phone_number'] = special.phone_number
        if hasattr(special, 'mobile_order_url') and special.mobile_order_url:
            required_fields['mobile_order_url'] = special.mobile_order_url
            
        # Fill in missing fields with current values
        for field, default_value in required_fields.items():
            if field not in post_data or not post_data[field]:
                post_data[field] = default_value
        
        # Clear CTA fields that shouldn't be set based on cta_choices
        cta_choice = post_data.get('cta_choices', 'order')
        if cta_choice != 'order':
            post_data['order_url'] = ''
        if cta_choice != 'call':
            post_data['phone_number'] = ''
        if cta_choice != 'mobile_order':
            post_data['mobile_order_url'] = ''
        
        # Create form with complete data
        form = SpecialForm(data=post_data, files=request.FILES, instance=special)
        
        if form.is_valid():
            updated_special = form.save()
            logger.info("Successfully saved special %s", updated_special.pk)
            return HttpResponse(status=204)  # Success, no content
        else:
            logger.debug("Form errors: %s", form.errors.as_json())
            # Return more detailed error information
            error_details = []
            for field, errors in form.errors.items():
                error_details.append(f"{field}: {', '.join(errors)}")
            return HttpResponseBadRequest(f"Form validation failed: {'; '.join(error_details)}")

    return HttpResponseBadRequest("Invalid request method")

