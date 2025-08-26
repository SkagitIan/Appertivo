from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
import json
import openai
import requests
import stripe
from dotenv import load_dotenv
load_dotenv()

from django.utils import timezone
from .models import (
    Special,
    Restaurant,
    Connection,
    UserProfile,
    EmailSignup,
    Article,
    Subscription,
    Transaction,
)
from .forms import SpecialForm
from app.integrations.google import *

def home(request):
    """Home page view"""
    return render(request, 'app/home.html')


def resources(request):
    """Resources page view."""
    articles = Article.objects.all()
    return render(request, 'app/resources.html', {"articles": articles})


def article_detail(request, slug):
    """Display a single article."""
    article = get_object_or_404(Article, slug=slug)
    return render(request, "app/article_detail.html", {"article": article})

def register_view(request):
    """Registration page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        restaurant_name = request.POST.get('restaurant_name')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'User with this email already exists.')
            return render(request, 'registration/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        
        # Create user profile
        profile = UserProfile.objects.create(
            user=user,
            restaurant_name=restaurant_name,
            is_email_verified=False
        )
        
        # Send verification email (for now, just mark as verified)
        profile.is_email_verified = True
        profile.save()
        
        messages.success(request, 'Account created successfully! You can now sign in.')
        return redirect('login')
    
    return render(request, 'registration/register.html')

def login_view(request):
    """Login page"""
    print("login page")
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'registration/login.html')

@login_required
def dashboard(request):
    code = request.GET.get("code")
    if code:
        # call our helper and save connection
        conn = complete_google_auth(request.user, code)
        if conn:
            logger.info("Google connection established for %s", request.user)
        else:
            logger.error("Google connection failed for %s", request.user)
        # after processing, you might want to redirect to clean the URL
        return redirect("dashboard")
    conn = Connection.objects.filter(
        user=request.user, platform="google_business", is_connected=True
    ).first()
    show_location_modal = False
    locations = []
    if conn:
        settings_data = conn.settings or {}
        if not settings_data.get("location_id"):
            show_location_modal = True
            locations = settings_data.get("locations", [])

    specials = Special.objects.filter(user=request.user)
    active_specials = specials.filter(status='active')

    total_email_signups = EmailSignup.objects.filter(restaurant=request.user).count()
    total_email_signups_from_specials = sum(special.email_signups for special in active_specials)

    stats = {
        'active': active_specials.count(),
        'views': sum(special.views for special in active_specials),
        'clicks': sum(special.clicks for special in active_specials),
        'email_signups': total_email_signups,
    }

    context = {
        'specials': specials[:3],  # Latest 3 for overview
        'stats': stats,
        'show_location_modal': show_location_modal,
        'google_locations': locations,
    }
    return render(request, 'app/dashboard.html', context)

# views.py
import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

@login_required
@require_http_methods(["POST"])
def subscribe(request):
    plan = request.POST.get("plan")
    price_lookup = {
        "pro": os.getenv("STRIPE_PRICE_PRO"),
        "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE"),
    }
    price_id = price_lookup.get(plan)
    if not price_id:
        messages.error(request, "Invalid plan selected.")
        return redirect("billing")

    stripe.api_key = os.getenv("STRIPE_API_KEY")

    # Ensure (or create) a Stripe Customer and persist the ID
    profile = request.user.profile
    if not profile.stripe_customer_id:
        customer = stripe.Customer.create(
            email=request.user.email,
            name=request.user.get_full_name() or request.user.username,
            metadata={"django_user_id": str(request.user.id)}
        )
        profile.stripe_customer_id = customer.id
        profile.save(update_fields=["stripe_customer_id"])

    session = stripe.checkout.Session.create(
        customer=profile.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        allow_promotion_codes=True,
        success_url=request.build_absolute_uri(reverse("billing")) + "?status=success",
        cancel_url=request.build_absolute_uri(reverse("billing")) + "?status=cancelled",
        subscription_data={
            "metadata": {"plan": plan, "django_user_id": request.user.id},
        },
        billing_address_collection="auto",
    )
    return redirect(session.url)

# views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # 1) Checkout completed -> has subscription + customer
    if event['type'] == 'checkout.session.completed':
        sess = event['data']['object']
        customer_id = sess.get('customer')
        subscription_id = sess.get('subscription')
        plan = (sess.get('metadata') or {}).get('plan')

        # Find the user by customer_id (or by sess.metadata.django_user_id)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        profile = Profile.objects.filter(stripe_customer_id=customer_id).select_related("user").first()
        if profile and plan and subscription_id:
            profile.subscription_tier = plan
            profile.save(update_fields=["subscription_tier"])
            Subscription.objects.update_or_create(
                user=profile.user,
                defaults={
                    "stripe_subscription_id": subscription_id,
                    "plan": plan,
                    "started_at": timezone.now(),
                    "canceled_at": None,
                },
            )

    # 2) Invoice paid -> book a Transaction
    if event['type'] == 'invoice.paid':
        inv = event['data']['object']
        customer_id = inv.get('customer')
        amount = (inv.get('amount_paid') or 0) / 100.0
        profile = Profile.objects.filter(stripe_customer_id=customer_id).select_related("user").first()
        if profile and hasattr(profile.user, "subscription"):
            Transaction.objects.create(
                subscription=profile.user.subscription,
                plan=profile.subscription.plan,
                amount=amount,
                status="paid",
                occurred_at=timezone.now(),
            )

    # 3) Subscription cancelled at Stripe side
    if event['type'] == 'customer.subscription.deleted':
        sub = event['data']['object']
        subscription_id = sub.get('id')
        s = Subscription.objects.filter(stripe_subscription_id=subscription_id).select_related("user").first()
        if s:
            s.canceled_at = timezone.now()
            s.save(update_fields=["canceled_at"])
            prof = s.user.profile
            prof.subscription_tier = "free"
            prof.save(update_fields=["subscription_tier"])

    return HttpResponse(status=200)


@login_required
def billing(request):
    """Display billing details and subscription options."""
    profile = request.user.profile

    subscription = getattr(request.user, "subscription", None)
    transactions = subscription.transactions.order_by("-occurred_at") if subscription else []

    plans = [
        {
            "tier": "pro",
            "name": "Pro",
            "price": 99,
            "features": ["Unlimited specials", "Priority support"],
            "border": "border-blue-500",
        },
        {
            "tier": "enterprise",
            "name": "Enterprise",
            "price": 299,
            "features": ["Unlimited specials", "Dedicated support", "Custom integrations"],
            "border": "border-green-500",
        },
    ]

    context = {
        "profile": profile,
        "subscription": subscription,
        "plans": plans,
        "transactions": transactions,
    }

    return render(request, "app/billing.html", context)


@login_required
@require_http_methods(["POST"])
def subscribe(request):
    """Subscribe the user to a plan using Stripe."""
    plan = request.POST.get("plan")
    plan_map = {
        "pro": {"product": "prod_SwKSitSvRgmuru", "price": 99},
        "enterprise": {"product": "prod_SwKTg5ev69mlPD", "price": 299},
    }
    if plan not in plan_map:
        messages.error(request, "Invalid plan selected.")
        return redirect("billing")

    stripe.api_key = os.getenv('STRIPE_API_KEY')
    try:
        price_data = stripe.Price.list(product=plan_map[plan]["product"], limit=1)
        price_id = price_data["data"][0]["id"]
        sub = stripe.Subscription.create(customer=request.user.email, items=[{"price": price_id}])

        profile = request.user.profile
        profile.subscription_tier = plan
        profile.save(update_fields=["subscription_tier"])

        subscription, _ = Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                "stripe_subscription_id": sub["id"],
                "plan": plan,
                "started_at": timezone.now(),
                "canceled_at": None,
            },
        )
        Transaction.objects.create(
            subscription=subscription,
            plan=plan,
            amount=plan_map[plan]["price"],
            status="paid",
        )


        messages.success(request, "Subscription updated successfully.")
        return redirect("dashboard")
    except Exception:
        messages.error(request, "Unable to process your subscription.")
        return redirect("billing")


@login_required
@require_http_methods(["POST"])
def cancel_subscription(request):
    """Cancel the user's subscription and revert to free tier."""
    profile = request.user.profile
    subscription = getattr(request.user, "subscription", None)
    if subscription:
        stripe.api_key = settings.STRIPE_API_KEY
        try:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        except Exception:
            pass
        subscription.canceled_at = timezone.now()
        subscription.save(update_fields=["canceled_at"])

    profile.subscription_tier = "free"
    profile.save(update_fields=["subscription_tier"])
    messages.success(request, "Subscription cancelled.")
    return redirect("billing")

@login_required
def specials_list(request):
    """List all specials"""
    specials = Special.objects.filter(user=request.user)
    return render(request, 'app/list.html', {'specials': specials})


@login_required
@require_http_methods(["POST"])
def special_unpublish(request, special_id):
    """Mark a special as expired."""
    special = get_object_or_404(Special, id=special_id, user=request.user)
    special.status = "expired"
    special.save(update_fields=["status"])
    return redirect("specials_list")


@login_required
@require_http_methods(["POST"])
def special_publish(request, special_id):
    """Republish an expired special."""
    special = get_object_or_404(Special, id=special_id, user=request.user)
    special.status = "active"
    special.save(update_fields=["status"])
    return redirect("specials_list")


@login_required
@require_http_methods(["POST"])
def special_delete(request, special_id):
    """Permanently delete a special."""
    special = get_object_or_404(Special, id=special_id, user=request.user)
    special.delete()
    return redirect("specials_list")


@login_required
@require_http_methods(["POST"])
def special_edit(request, special_id):
    """Update a special's fields."""
    special = get_object_or_404(Special, id=special_id, user=request.user)
    form = SpecialForm(request.POST, request.FILES, instance=special)
    if form.is_valid():
        form.save()
    return redirect("specials_list")

@login_required
def create_special(request):
    """Create a new special"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        cta_type = request.POST.get('cta_type', 'web')
        cta_url = request.POST.get('cta_url', '') if cta_type == 'web' else None
        cta_phone = request.POST.get('cta_phone', '') if cta_type == 'call' else None
        image = request.FILES.get('image')
        
        special = Special.objects.create(
            user=request.user,
            title=title,
            description=description,
            price=price,
            start_date=start_date,
            end_date=end_date,
            cta_type=cta_type,
            cta_url=cta_url,
            cta_phone=cta_phone,
            image=image,
            status='active'
        )
        # Send email notifications to subscribers
        send_special_notification(special)
        # Publish to Google if connected
        publish_special(special)
        
        messages.success(request, 'Special created successfully!')
        return redirect('specials_list')
    
    return render(request, 'app/create.html')

@login_required
@csrf_exempt
def enhance_description(request):
    """Enhance description using OpenAI"""
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')
        price = data.get('price')
        
        if not settings.OPENAI_API_KEY:
            return JsonResponse({'error': 'OpenAI API key not configured'})
        
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a restaurant marketing expert. Enhance the description of daily specials to be more appetizing and compelling while keeping them concise. Focus on sensory details, cooking methods, and what makes the dish special. Return only the enhanced description."
                    },
                    {
                        "role": "user",
                        "content": f"""Enhance this restaurant special description:
                        
Title: {title}
Current Description: {description}
Price: ${price}

Make it more appealing and mouth-watering while keeping it under 150 characters. Focus on ingredients, preparation, and what makes it special."""
                    }
                ],
                max_tokens=200,
                temperature=0.7,
            )
            
            enhanced_description = response.choices[0].message.content.strip()
            return JsonResponse({'description': enhanced_description})
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})

@login_required
def connections(request):
    """Manage platform connections"""
    user_connections = Connection.objects.filter(user=request.user)

    # Create default connections if they don't exist
    platforms = ['website', 'google_business', 'pos', 'delivery']
    for platform in platforms:
        Connection.objects.get_or_create(
            user=request.user,
            platform=platform,
            defaults={'is_connected': platform == 'website'}  # Website is always connected
        )

    if request.method == 'POST' and request.POST.get('platform') == 'google_business':
        conn = Connection.objects.get(user=request.user, platform='google_business')
        settings_data = conn.settings or {}
        location_id = request.POST.get('location_id')
        if location_id:
            settings_data['location_id'] = location_id
            for loc in settings_data.get('locations', []):
                if loc.get('id') == location_id:
                    settings_data['location_name'] = loc.get('name')
                    if 'address' in loc:
                        settings_data['location_address'] = loc['address']
                    break
        settings_data['delete_when_expired'] = request.POST.get('delete_when_expired') == 'on'
        conn.settings = settings_data
        conn.save()
        return redirect('connections')

    connections_data = Connection.objects.filter(user=request.user)
    return render(request, 'app/connections.html', {'connections': connections_data})


@login_required
def google_connect(request):
    """Start the Google OAuth flow."""
    auth_url = get_authorization_url()
    return HttpResponseRedirect(auth_url)


@login_required
def google_callback(request):
    """Handle Google OAuth callback and store credentials."""
    code = request.GET.get("code")
    if not code:
        return redirect("connections")
    token_data = exchange_code_for_tokens(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    account_id, account_name, locations, raw_locations = get_accounts_and_locations(access_token)
    connection, _ = Connection.objects.get_or_create(
        user=request.user, platform="google_business"
    )
    connection.is_connected = True
    connection.settings = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "account_id": account_id,
        "account_name": account_name,
        "locations": locations,
        "locations_raw": raw_locations,
        "delete_when_expired": True,
    }
    connection.save()
    return redirect("connections")


@login_required
@require_http_methods(["POST"])
def select_google_location(request):
    """Persist the user's chosen Google location."""
    conn = Connection.objects.get(user=request.user, platform="google_business")
    settings_data = conn.settings or {}
    location_id = request.POST.get("location_id")
    if location_id:
        settings_data["location_id"] = location_id
        for loc in settings_data.get("locations", []):
            if loc.get("id") == location_id:
                settings_data["location_name"] = loc.get("name")
                if "address" in loc:
                    settings_data["location_address"] = loc["address"]
                break
    conn.settings = settings_data
    conn.save()
    return redirect("dashboard")

def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('home')

# Widget System Views
def widget_special(request, user_id):
    """API endpoint for widget to get today's special"""
    try:
        user = get_object_or_404(User, id=user_id)
        # Get today's active special
        from django.utils import timezone
        now = timezone.now()
        special = Special.objects.filter(
            user=user,
            status='active',
            start_date__lte=now,
            end_date__gte=now
        ).first()
        
        if special:
            # Increment view count
            special.views += 1
            special.save()
            
            data = {
                'id': str(special.id),
                'title': special.title,
                'description': special.description,
                'price': str(special.price),
                'image': request.build_absolute_uri(special.image.url) if special.image else None,
                'cta_type': special.cta_type,
                'cta_url': special.cta_url,
                'cta_phone': special.cta_phone,
                'restaurant_name': user.username,
            }
            return JsonResponse({'special': data})
        else:
            return JsonResponse({'special': None})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def widget_signup(request, user_id):
    """Email signup endpoint for widget"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            special_id = data.get('special_id')
            
            if not email:
                return JsonResponse({'error': 'Email required'}, status=400)
                
            user = get_object_or_404(User, id=user_id)
            special = None
            if special_id:
                special = Special.objects.filter(id=special_id, user=user).first()
            
            # Create or get email signup
            signup, created = EmailSignup.objects.get_or_create(
                restaurant=user,
                email=email,
                defaults={'special': special}
            )
            
            if created and special:
                # Increment email signup count on special
                special.email_signups += 1
                special.save()
                
            return JsonResponse({'success': True, 'created': created})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST required'}, status=405)

def widget_js(request, user_id):
    """Generate JavaScript widget code"""
    user = get_object_or_404(User, id=user_id)
    restaurant_name = user.username

    widget_code = f"""
(function() {{
    const WIDGET_API_URL = 'https://appertivo.com/widget/';
    const USER_ID = '{user_id}';
    const RESTAURANT_NAME = '{restaurant_name}';

    function createWidget() {{
        const widgetContainer = document.getElementById('appertivo-widget');
        if (!widgetContainer) return;

        // Widget styles
        const style = document.createElement('style');
        style.textContent = `
            .appertivo-widget-button {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #3b82f6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 9999px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                cursor: pointer;
                z-index: 9999;
            }}
            .appertivo-widget-panel {{
                position: fixed;
                bottom: 80px;
                right: 20px;
                width: 320px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
                display: none;
                z-index: 9999;
            }}
            .appertivo-widget {{
                max-width: 400px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            .appertivo-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px;
                text-align: center;
            }}
            .appertivo-content {{
                padding: 20px;
            }}
            .appertivo-special {{
                text-align: center;
            }}
            .appertivo-image {{
                width: 100%;
                height: 200px;
                object-fit: cover;
                border-radius: 8px;
                margin-bottom: 12px;
            }}
            .appertivo-title {{
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 8px;
                color: #1f2937;
            }}
            .appertivo-description {{
                color: #6b7280;
                margin-bottom: 12px;
                line-height: 1.5;
            }}
            .appertivo-price {{
                font-size: 24px;
                font-weight: bold;
                color: #059669;
                margin-bottom: 16px;
            }}
            .appertivo-cta {{
                display: inline-block;
                background: #3b82f6;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 500;
                margin-bottom: 16px;
            }}
            .appertivo-signup {{
                border-top: 1px solid #e5e7eb;
                padding-top: 16px;
                margin-top: 16px;
            }}
            .appertivo-signup-form {{
                display: flex;
                gap: 8px;
            }}
            .appertivo-email {{
                flex: 1;
                padding: 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
            }}
            .appertivo-subscribe {{
                background: #059669;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
            }}
            .appertivo-no-special {{
                text-align: center;
                padding: 40px 20px;
                color: #6b7280;
            }}
        `;
        document.head.appendChild(style);

        widgetContainer.className = 'appertivo-widget-panel';
        widgetContainer.style.display = 'none';
        document.body.appendChild(widgetContainer);

        const launcher = document.createElement('button');
        launcher.className = 'appertivo-widget-button';
        launcher.textContent = "Today's Special";
        launcher.addEventListener('click', () => {{
            widgetContainer.style.display = widgetContainer.style.display === 'none' || !widgetContainer.style.display ? 'block' : 'none';
        }});
        document.body.appendChild(launcher);

        // Fetch today's special
        fetch(WIDGET_API_URL + USER_ID + '/special/')
            .then(response => response.json())
            .then(data => {{
                if (data.special) {{
                    const special = data.special;
                    widgetContainer.innerHTML = `
                        <div class="appertivo-widget">
                            <div class="appertivo-header">
                                <h3>Today's Special at ${{special.restaurant_name}}</h3>
                            </div>
                            <div class="appertivo-content">
                                <div class="appertivo-special">
                                    ${{special.image ? `<img src="${{special.image}}" alt="${{special.title}}" class="appertivo-image">` : ''}}
                                    <div class="appertivo-title">${{special.title}}</div>
                                    <div class="appertivo-description">${{special.description}}</div>
                                    <div class="appertivo-price">$${{special.price}}</div>
                                    ${{special.cta_type === 'web' && special.cta_url ? 
                                        `<a href="${{special.cta_url}}" class="appertivo-cta" target="_blank">Order Online</a>` :
                                        special.cta_type === 'call' && special.cta_phone ? 
                                        `<a href="tel:${{special.cta_phone}}" class="appertivo-cta">Call to Order</a>` : ''
                                    }}
                                </div>
                                <div class="appertivo-signup">
                                    <p style="margin-bottom: 8px; font-size: 14px; color: #6b7280;">
                                        Get notified about future specials:
                                    </p>
                                    <form class="appertivo-signup-form" onsubmit="submitSignup(event, '${{special.id}}')">
                                        <input type="email" class="appertivo-email" placeholder="Enter your email" required>
                                        <button type="submit" class="appertivo-subscribe">Subscribe</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    `;
                }} else {{
                    widgetContainer.innerHTML = `
                        <div class="appertivo-widget">
                            <div class="appertivo-header">
                                <h3>${{RESTAURANT_NAME}}</h3>
                            </div>
                            <div class="appertivo-no-special">
                                <p>No special available today.</p>
                                <p>Check back soon!</p>
                            </div>
                        </div>
                    `;
                }}
            }})
            .catch(err => {{
                console.error('Widget error:', err);
                widgetContainer.innerHTML = '<p>Unable to load special</p>';
            }});
    }}
    
    window.submitSignup = function(event, specialId) {{
        event.preventDefault();
        const email = event.target.querySelector('.appertivo-email').value;
        
        fetch(WIDGET_API_URL + USER_ID + '/signup/', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                email: email,
                special_id: specialId
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                event.target.innerHTML = `
                    <div style="text-align: center; color: #059669; font-weight: 500;">
                        ✓ Successfully subscribed!
                    </div>
                `;
            }} else {{
                alert('Signup failed: ' + (data.error || 'Unknown error'));
            }}
        }})
        .catch(err => {{
            console.error('Signup error:', err);
            alert('Signup failed');
        }});
    }};
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', createWidget);
    }} else {{
        createWidget();
    }}
}})();
"""
    return HttpResponse(widget_code, content_type='application/javascript')

@login_required
def widget_setup(request):
    """Widget setup page"""
    widget_js_url = f"https://appertivo.com/widget/{request.user.id}/js/"
    return render(request, 'app/widget_setup.html', {'widget_js_url': widget_js_url})

from datetime import datetime

def send_special_notification(special):
    """Send email notifications to all subscribers when a new special is published"""
    subscribers = EmailSignup.objects.filter(restaurant=special.user, is_active=True)
    from django.utils.dateparse import parse_datetime, parse_date

    start = parse_datetime(special.start_date) or parse_date(special.start_date)
    end = parse_datetime(special.end_date) or parse_date(special.end_date)
    if not subscribers.exists():
        return
    
    restaurant_name = special.user.profile.restaurant_name if hasattr(special.user, 'profile') else special.user.username
    
    # Prepare email content
    subject = f"🍽️ New Special at {restaurant_name}: {special.title}"
    
    # Create HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }}
            .special-image {{ width: 100%; height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 20px; }}
            .special-title {{ font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #1f2937; }}
            .special-description {{ margin-bottom: 20px; color: #6b7280; }}
            .special-price {{ font-size: 28px; font-weight: bold; color: #059669; margin-bottom: 25px; }}
            .cta-button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: 500; }}
            .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>New Special at {restaurant_name}!</h1>
                <p>Check out what's delicious today</p>
            </div>
            <div class="content">
                {f'<img src="{special.image.url}" alt="{special.title}" class="special-image">' if special.image else ''}
                <div class="special-title">{special.title}</div>
                <div class="special-description">{special.description}</div>
                <div class="special-price">${special.price}</div>
                
                {f'<a href="{special.cta_url}" class="cta-button">Order Online</a>' if special.cta_type == 'web' and special.cta_url else ''}
                {f'<a href="tel:{special.cta_phone}" class="cta-button">Call to Order</a>' if special.cta_type == 'call' and special.cta_phone else ''}
                
                <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
                    Available from {start} until {end}
                </p>
            </div>
            <div class="footer">
                <p>You're receiving this because you subscribed to {restaurant_name}'s specials.</p>
                <p style="font-size: 12px;">Powered by Appertivo</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    New Special at {restaurant_name}!
    
    {special.title}
    
    {special.description}
    
    Price: ${special.price}
    
    {'Order online: ' + special.cta_url if special.cta_type == 'web' and special.cta_url else ''}
    {'Call to order: ' + special.cta_phone if special.cta_type == 'call' and special.cta_phone else ''}
    
    Available from {start} until {end}
    
    ---
    You're receiving this because you subscribed to {restaurant_name}'s specials.
    Powered by Appertivo
    """
    
    # Send emails to all subscribers
    emails_sent = 0
    for subscriber in subscribers:
        try:
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@appertivo.com',
                to=[subscriber.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            emails_sent += 1
        except Exception as e:
            print(f"Failed to send email to {subscriber.email}: {e}")
    
    print(f"Sent {emails_sent} email notifications for special: {special.title}")

@login_required
def email_analytics(request):
    """Email analytics page"""
    signups = EmailSignup.objects.filter(restaurant=request.user)
    total_signups = signups.count()
    
    # Get signup stats per special
    specials_stats = []
    specials = Special.objects.filter(user=request.user).order_by('-created_at')
    
    for special in specials:
        special_signups = signups.filter(special=special).count()
        specials_stats.append({
            'special': special,
            'signups': special_signups,
            'total_signups': special.email_signups
        })
    
    context = {
        'total_signups': total_signups,
        'recent_signups': signups.order_by('-signed_up_at')[:10],
        'specials_stats': specials_stats,
    }
    
    return render(request, 'app/email_analytics.html', context)

def demo_widget(request):
    """Demo widget endpoint for homepage visitors"""
    # Create a sample special for demo purposes
    demo_special = {
        'id': 'demo-special',
        'title': 'Truffle Mushroom Risotto',
        'description': 'Creamy Arborio rice slow-cooked with wild mushrooms, finished with truffle oil and Parmesan. A rich, earthy flavor that melts in your mouth.',
        'price': '28.50',
        'image': None,  # Could add a demo image URL here
        'cta_type': 'web',
        'cta_url': 'https://example-restaurant.com/order',
        'cta_phone': None,
        'restaurant_name': 'Demo Restaurant',
    }
    
    return JsonResponse({'special': demo_special})

@csrf_exempt
def demo_widget_signup(request):
    """Demo email signup - doesn't actually save anything"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({'error': 'Email required'}, status=400)
            
            # For demo purposes, always return success
            return JsonResponse({'success': True, 'created': True, 'demo': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST required'}, status=405)

def demo_widget_js(request):
    """Generate JavaScript for demo widget"""
    widget_code = f"""
(function() {{
    const WIDGET_API_URL = '{request.build_absolute_uri("/demo-widget/")}';
    const RESTAURANT_NAME = 'Demo Restaurant';

    function createDemoWidget() {{
        const widgetContainer = document.getElementById('appertivo-demo-widget');
        if (!widgetContainer) return;
        
        // Widget styles
        const style = document.createElement('style');
        style.textContent = `
            .appertivo-widget {{
                max-width: 400px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0 auto;
            }}
            .appertivo-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px;
                text-align: center;
            }}
            .appertivo-content {{
                padding: 20px;
            }}
            .appertivo-special {{
                text-align: center;
            }}
            .appertivo-image {{
                width: 100%;
                height: 200px;
                object-fit: cover;
                border-radius: 8px;
                margin-bottom: 12px;
            }}
            .appertivo-title {{
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 8px;
                color: #1f2937;
            }}
            .appertivo-description {{
                color: #6b7280;
                margin-bottom: 12px;
                line-height: 1.5;
            }}
            .appertivo-price {{
                font-size: 24px;
                font-weight: bold;
                color: #059669;
                margin-bottom: 16px;
            }}
            .appertivo-cta {{
                display: inline-block;
                background: #3b82f6;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 500;
                margin-bottom: 16px;
            }}
            .appertivo-signup {{
                border-top: 1px solid #e5e7eb;
                padding-top: 16px;
                margin-top: 16px;
            }}
            .appertivo-signup-form {{
                display: flex;
                gap: 8px;
            }}
            .appertivo-email {{
                flex: 1;
                padding: 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
            }}
            .appertivo-subscribe {{
                background: #059669;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
            }}
            .appertivo-demo-badge {{
                position: absolute;
                top: 8px;
                right: 8px;
                background: #f59e0b;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }}
        `;
        document.head.appendChild(style);
        
        // Fetch demo special
        fetch(WIDGET_API_URL + 'special/')
            .then(response => response.json())
            .then(data => {{
                if (data.special) {{
                    const special = data.special;
                    widgetContainer.innerHTML = `
                        <div class="appertivo-widget" style="position: relative;">
                            <div class="appertivo-demo-badge">DEMO</div>
                            <div class="appertivo-header">
                                <h3>Today's Special at ${{special.restaurant_name}}</h3>
                            </div>
                            <div class="appertivo-content">
                                <div class="appertivo-special">
                                    ${{special.image ? `<img src="${{special.image}}" alt="${{special.title}}" class="appertivo-image">` : ''}}
                                    <div class="appertivo-title">${{special.title}}</div>
                                    <div class="appertivo-description">${{special.description}}</div>
                                    <div class="appertivo-price">$${{special.price}}</div>
                                    ${{special.cta_type === 'web' && special.cta_url ? 
                                        `<a href="#" onclick="alert('This is a demo - button would normally link to ordering page'); return false;" class="appertivo-cta">Order Online</a>` :
                                        special.cta_type === 'call' && special.cta_phone ? 
                                        `<a href="#" onclick="alert('This is a demo - button would normally call restaurant'); return false;" class="appertivo-cta">Call to Order</a>` : ''
                                    }}
                                </div>
                                <div class="appertivo-signup">
                                    <p style="margin-bottom: 8px; font-size: 14px; color: #6b7280;">
                                        Get notified about future specials:
                                    </p>
                                    <form class="appertivo-signup-form" onsubmit="submitDemoSignup(event, '${{special.id}}')">
                                        <input type="email" class="appertivo-email" placeholder="Enter your email" required>
                                        <button type="submit" class="appertivo-subscribe">Subscribe</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    `;
                }}
            }})
            .catch(err => {{
                console.error('Demo widget error:', err);
                widgetContainer.innerHTML = '<p>Unable to load demo widget</p>';
            }});
    }}
    
    window.submitDemoSignup = function(event, specialId) {{
        event.preventDefault();
        const email = event.target.querySelector('.appertivo-email').value;
        
        fetch(WIDGET_API_URL + 'signup/', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                email: email,
                special_id: specialId
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                event.target.innerHTML = `
                    <div style="text-align: center; color: #059669; font-weight: 500;">
                        ✓ Demo signup successful! (Not actually saved)
                    </div>
                `;
            }} else {{
                alert('Demo signup failed');
            }}
        }})
        .catch(err => {{
            console.error('Demo signup error:', err);
            alert('Demo signup failed');
        }});
    }};
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', createDemoWidget);
    }} else {{
        createDemoWidget();
    }}
}})();
"""
    return HttpResponse(widget_code, content_type='application/javascript')
