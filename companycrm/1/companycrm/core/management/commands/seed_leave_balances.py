from __future__ import annotations

from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import (
    Profile,
    LeaveBalanceAdjustment,
    leave_year_stats,
)

ANNUAL_CAP = Decimal("30.0")  # target accrued for the year

class Command(BaseCommand):
    help = "Top up each user's accrued days to the annual cap (30) for a given year using adjustments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=date.today().year,
            help="Calendar year to set (default: current year).",
        )
        parser.add_argument(
            "--reason",
            type=str,
            default="Initial annual grant",
            help="Reason stored on each adjustment.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without writing to the database.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        year = opts["year"]
        reason = opts["reason"]
        dry_run = opts["dry_run"]

        User = get_user_model()

        created = 0
        skipped = 0
        preview_rows = []

        for user in User.objects.filter(is_active=True).select_related("profile"):
            profile = getattr(user, "profile", None)
            if not profile:
                skipped += 1
                continue

            stats = leave_year_stats(user, year=year)
            accrued = Decimal(str(stats["accrued"]))

            if accrued >= ANNUAL_CAP:
                skipped += 1
                continue

            delta = (ANNUAL_CAP - accrued).quantize(Decimal("0.01"))
            preview_rows.append((user.username, float(accrued), float(delta)))

            if not dry_run:
                LeaveBalanceAdjustment.objects.create(
                    user_profile=profile,
                    year=year,
                    delta_days=delta,
                    reason=reason,
                    created_by=None,  # you can fill with a service user if preferred
                )
                created += 1

        # Summary output
        if preview_rows:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Year {year} top-up preview:"))
            for uname, accrued, delta in preview_rows:
                self.stdout.write(f" - {uname}: accrued={accrued:.2f} -> +{delta:.2f}d")
        else:
            self.stdout.write("No users require top-up (all already at or above 30.00).")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: no adjustments were written."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Created {created} adjustments; skipped {skipped}."))
