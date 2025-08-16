"""Management command to remove orphaned anonymous profiles."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from profiles.models import UserProfile


class Command(BaseCommand):
    """Delete anonymous profiles with no related activity."""

    help = "Prune anonymous UserProfile objects without related specials or signups."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Age in days after which an orphaned profile is deleted.",
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        qs = (
            UserProfile.objects.filter(
                user__isnull=True,
                specials__isnull=True,
                email_signups__isnull=True,
                created_at__lt=cutoff,
            )
            .distinct()
        )
        count = qs.count()
        qs.delete()
        self.stdout.write(f"Deleted {count} orphaned profiles.")
