from datetime import timedelta
from django.db.models import Sum, IntegerField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Special, EmailSignup, Integration


def settings_modal(request):
    """Provide context data for the global settings modal."""
    if not request.user.is_authenticated:
        return {}

    profile = request.user.userprofile
    specials = Special.objects.filter(user_profile=profile)
    today = timezone.localdate()

    stats = specials.aggregate(
        opens=Coalesce(Sum("analytics__opens"), Value(0), output_field=IntegerField()),
        cta_clicks=Coalesce(Sum("analytics__cta_clicks"), Value(0), output_field=IntegerField()),
        email_signups=Coalesce(Sum("analytics__email_signups"), Value(0), output_field=IntegerField()),
    )
    opens = stats["opens"] or 0
    clicks = stats["cta_clicks"] or 0
    stats["ctr"] = round((clicks / opens) * 100, 1) if opens else 0.0

    qs_signups = EmailSignup.objects.filter(user_profile=profile)
    signups_today = qs_signups.filter(created_at__date=today).count()
    signups_7d = qs_signups.filter(created_at__date__gte=today - timedelta(days=6)).count()
    signups_30d = qs_signups.filter(created_at__date__gte=today - timedelta(days=29)).count()

    stats.update(
        {
            "signups_today": signups_today,
            "signups_7d": signups_7d,
            "signups_30d": signups_30d,
        }
    )

    top_special = (
        specials.exclude(analytics__isnull=True)
        .order_by("-analytics__cta_clicks", "-analytics__opens")
        .first()
    )

    integration_status = {
        i.provider: i.enabled for i in Integration.objects.filter(user_profile=profile)
    }

    return {
        "profile": profile,
        "specials": specials.select_related("analytics"),
        "top_special": top_special,
        "stats": stats,
        "integration_status": integration_status,
    }
