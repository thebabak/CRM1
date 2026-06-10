# core/models.py
from __future__ import annotations

from datetime import date, datetime
from django.conf import settings
from django.db import models
from django.utils import timezone


# =========================
# Org structure
# =========================
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Role(models.IntegerChoices):
    # Increasing numbers = increasing seniority
    EMPLOYEE = 1, "Employee"
    MIDDLE = 2, "Middle Management"
    EXECUTIVE = 3, "Executive Management"  # reserved for future
    BOARD = 4, "Board of Directors"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    employee_id = models.CharField(max_length=50, unique=True)
    role = models.IntegerField(choices=Role.choices, default=Role.EMPLOYEE)
    position = models.ForeignKey(
        Position, null=True, blank=True, on_delete=models.SET_NULL, related_name="profiles"
    )
    departments = models.ManyToManyField(Department, blank=True, related_name="profiles")

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.get_role_display()})"


# =========================
# Request + Approvals
# =========================
class RequestStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    IN_REVIEW = "IN_REVIEW", "In Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


def _role_of(user) -> int | None:
    prof = getattr(user, "profile", None)
    return getattr(prof, "role", None) if prof else None


class Request(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requests_created"
    )
    created_at = models.DateTimeField(default=timezone.now)

    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.DRAFT
    )

    # Workflow:
    # - If required_user is set → that specific user (replacement) must act first.
    # - After replacement approves → MIDDLE → BOARD.
    # - required_role mirrors "who is up next".
    required_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests_waiting_on_me",
        help_text="If set, this specific user must act before role-based approvals.",
    )
    required_role = models.IntegerField(
        choices=Role.choices, default=Role.MIDDLE, help_text="Role required to act next."
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} [{self.status}]"

    # Invariants
    def save(self, *args, **kwargs):
        # Keep required_role in sync with the targeted user (if any).
        if self.required_user_id:
            r = _role_of(self.required_user)
            if r is not None:
                self.required_role = r
        super().save(*args, **kwargs)

    def is_terminal(self) -> bool:
        return self.status in (RequestStatus.APPROVED, RequestStatus.REJECTED)

    # Submission / routing
    def submit(self) -> None:
        """
        DRAFT → SUBMITTED.
        Order: Replacement (if present) → MIDDLE → BOARD.
        If a typed payload (e.g., LeaveRequest) has a replacement, use them.
        """
        if self.status != RequestStatus.DRAFT:
            return

        replacement = self.required_user
        if not replacement and hasattr(self, "leave") and self.leave.replacement:
            replacement = self.leave.replacement

        if replacement:
            self.required_user = replacement
            self.required_role = _role_of(replacement) or Role.MIDDLE
        else:
            self.required_user = None
            self.required_role = Role.MIDDLE

        self.status = RequestStatus.SUBMITTED
        self.save(update_fields=["required_user", "required_role", "status"])


class Decision(models.TextChoices):
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"


class Approval(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="approvals")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approvals_made"
    )
    decided_role = models.IntegerField(choices=Role.choices, null=True, blank=True)
    decision = models.CharField(max_length=10, choices=Decision.choices)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["decided_at"]

    def __str__(self) -> str:
        return f"{self.get_decision_display()} by {self.decided_by} @ {self.decided_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        # Prevent adding approvals to finalized requests
        if self.request.status in (RequestStatus.APPROVED, RequestStatus.REJECTED):
            from django.core.exceptions import ValidationError
            raise ValidationError("Cannot add approvals to a finalized request.")
        super().save(*args, **kwargs)


# ---------- Workflow helpers ----------
def _share_department(user_a, user_b) -> bool:
    pa = getattr(user_a, "profile", None)
    pb = getattr(user_b, "profile", None)
    if not pa or not pb:
        return False
    a = set(pa.departments.values_list("pk", flat=True))
    b = set(pb.departments.values_list("pk", flat=True))
    return bool(a & b)


def can_user_approve(user, req: Request) -> bool:
    """
    Replacement → Middle (same department) → Board.
    """
    if req.is_terminal():
        return False
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True

    uprof = getattr(user, "profile", None)
    cprof = getattr(req.created_by, "profile", None)
    if not uprof or not cprof:
        return False

    # Replacement step (targeted)
    if req.required_user_id:
        return user.pk == req.required_user_id

    # Role steps
    if req.required_role == Role.MIDDLE:
        return uprof.role == Role.MIDDLE and _share_department(user, req.created_by)

    if req.required_role == Role.BOARD:
        return uprof.role == Role.BOARD

    return False


def apply_decision(user, req: Request, decision: str, comment: str = "") -> None:
    """
    Replacement → Middle → Board → Approved.
    Any REJECT immediately finalizes.
    """
    if req.is_terminal():
        raise PermissionError("This request is already finalized.")
    if not can_user_approve(user, req):
        raise PermissionError("You are not allowed to act on this request.")

    Approval.objects.create(
        request=req,
        decided_by=user,
        decided_role=_role_of(user),
        decision=decision,
        comment=comment or "",
    )

    if decision == Decision.REJECT:
        req.status = RequestStatus.REJECTED
        req.required_user = None
        req.save(update_fields=["status", "required_user"])
        return

    # APPROVE path
    if req.required_user_id:
        # Replacement approved → Middle
        req.required_user = None
        req.required_role = Role.MIDDLE
        req.status = RequestStatus.IN_REVIEW
        req.save(update_fields=["required_user", "required_role", "status"])
        return

    if req.required_role == Role.MIDDLE:
        # Middle approved → Board
        req.required_role = Role.BOARD
        req.status = RequestStatus.IN_REVIEW
        req.save(update_fields=["required_role", "status"])
        return

    if req.required_role == Role.BOARD:
        # Final approval
        req.status = RequestStatus.APPROVED
        req.save(update_fields=["status"])
        return


# =========================
# Leave request (typed payload) + balances
# =========================
class LeaveType(models.TextChoices):
    PAID = "PAID", "Paid Leave"
    SICK = "SICK", "Sick Leave"
    EMERGENCY = "EMERGENCY", "Emergency Leave"


class LeaveMode(models.TextChoices):
    DAILY = "DAILY", "Daily"
    HOURLY = "HOURLY", "Hourly"


WORKING_HOURS_PER_DAY = 8  # adjust if needed


class LeaveRequest(models.Model):
    base_request = models.OneToOneField(
        Request, on_delete=models.CASCADE, related_name="leave"
    )

    # Snapshot of identity
    position = models.CharField(max_length=100, blank=True)
    personnel_code = models.CharField(max_length=50, blank=True)
    full_name = models.CharField(max_length=150, blank=True)

    leave_type = models.CharField(max_length=12, choices=LeaveType.choices)
    mode = models.CharField(max_length=8, choices=LeaveMode.choices)

    # DAILY
    daily_from = models.DateField(null=True, blank=True)
    daily_to = models.DateField(null=True, blank=True)
    duration_days = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # HOURLY
    hourly_date = models.DateField(null=True, blank=True)
    hourly_from = models.TimeField(null=True, blank=True)
    hourly_to = models.TimeField(null=True, blank=True)

    # First approver (validated in forms to be same layer, one dept, etc.)
    replacement = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leave_replacements",
        help_text="The person who will cover; they approve first.",
    )

    # Optional HR box
    remaining_monthly_days = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Leave #{self.pk} ({self.get_leave_type_display()} · {self.get_mode_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.mode == LeaveMode.DAILY:
            if not (self.daily_from and self.daily_to):
                raise ValidationError("Daily leave requires 'from' and 'to' dates.")
        if self.mode == LeaveMode.HOURLY:
            if not (self.hourly_date and self.hourly_from and self.hourly_to):
                raise ValidationError("Hourly leave requires date, from, and to times.")

    # ---- balance helpers on the instance ----
    def requested_days(self) -> float:
        """
        DAILY: prefer duration_days, else (to - from + 1).
        HOURLY: convert hours to day fraction.
        """
        if self.mode == LeaveMode.DAILY:
            if self.duration_days:
                return float(self.duration_days)
            if self.daily_from and self.daily_to:
                return float((self.daily_to - self.daily_from).days + 1)
            return 0.0
        if self.mode == LeaveMode.HOURLY:
            if self.hourly_date and self.hourly_from and self.hourly_to:
                dt_from = datetime.combine(self.hourly_date, self.hourly_from)
                dt_to = datetime.combine(self.hourly_date, self.hourly_to)
                hours = max(0.0, (dt_to - dt_from).total_seconds() / 3600.0)
                return hours / float(WORKING_HOURS_PER_DAY)
            return 0.0
        return 0.0


# --- Admin-adjustable leave balance deltas (FK to Profile so we can inline on Profile admin) ---
class LeaveBalanceAdjustment(models.Model):
    """
    Admin-entered deltas that tweak a user's annual balance.
    Positive = grant extra days; Negative = deduct days.
    Applied on top of normal accrual (2.5/month, cap 30).
    """
    user_profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="leave_adjustments"
    )
    year = models.PositiveIntegerField(help_text="Calendar year this adjustment applies to (e.g., 2025).")
    delta_days = models.DecimalField(max_digits=5, decimal_places=2, help_text="Use + to grant, − to deduct.")
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="leave_adjustments_created"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.delta_days >= 0 else ""
        return f"{self.user_profile.user} · {self.year} · {sign}{self.delta_days}d"


# ---- global balance helpers ----
from django.db.models import Sum, Q  # keep import near usage

def _clamp_days_to_year(start: date, end: date, year: int) -> float:
    """Clamp [start, end] inclusive to the given year and return number of calendar days."""
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    s = max(start, year_start)
    e = min(end, year_end)
    if e < s:
        return 0.0
    return float((e - s).days + 1)


def leave_year_stats(user, year: int | None = None, as_of: date | None = None) -> dict:
    """
    Compute live leave stats for a user for a given calendar year.

    Accrual policy:
      - 2.5 days per elapsed month
      - Capped at 30 days per year
      - Plus/minus admin adjustments for that year (FK via Profile)

    Used:
      - Sum of APPROVED leaves in that year
      - DAILY: inclusive day count, clamped to the year when ranges cross boundaries
      - HOURLY: hours converted to day fraction (uses WORKING_HOURS_PER_DAY)

    Returns:
      {"year": int, "accrued": float, "used": float, "remaining": float}
    """
    if as_of is None:
        as_of = date.today()
    if year is None:
        year = as_of.year

    # Months elapsed for accrual
    if year < as_of.year:
        months_elapsed = 12
    elif year == as_of.year:
        months_elapsed = as_of.month
    else:
        months_elapsed = 0  # future year: no accrual yet

    accrued = min(2.5 * months_elapsed, 30.0)

    # --- Admin adjustments (apply to accrued pool) ---
    profile = getattr(user, "profile", None)
    if profile:
        adj_total = (
            LeaveBalanceAdjustment.objects
            .filter(user_profile=profile, year=year)
            .aggregate(total=Sum("delta_days"))["total"]
            or 0.0
        )
    else:
        adj_total = 0.0

    accrued = float(accrued) + float(adj_total)

    # --- Used days in this year (only APPROVED requests) ---
    qs = (
        LeaveRequest.objects
        .select_related("base_request")
        .filter(base_request__created_by=user, base_request__status=RequestStatus.APPROVED)
        .filter(
            Q(mode=LeaveMode.DAILY, daily_from__year__lte=year, daily_to__year__gte=year) |
            Q(mode=LeaveMode.HOURLY, hourly_date__year=year)
        )
    )

    used = 0.0
    for lr in qs:
        if lr.mode == LeaveMode.DAILY and lr.daily_from and lr.daily_to:
            used += _clamp_days_to_year(lr.daily_from, lr.daily_to, year)
        elif lr.mode == LeaveMode.HOURLY and lr.hourly_date and lr.hourly_from and lr.hourly_to:
            dt_from = datetime.combine(lr.hourly_date, lr.hourly_from)
            dt_to = datetime.combine(lr.hourly_date, lr.hourly_to)
            hours = max(0.0, (dt_to - dt_from).total_seconds() / 3600.0)
            used += hours / float(WORKING_HOURS_PER_DAY)

    accrued = round(float(accrued), 2)
    used = round(float(used), 2)
    remaining = max(0.0, round(accrued - used, 2))

    return {"year": year, "accrued": accrued, "used": used, "remaining": remaining}


# =========================
# Signals: auto-create Profile
# =========================
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_user(sender, instance, created, **kwargs):
    """
    Auto-create a Profile for each new user if missing.
    Default role = EMPLOYEE; employee_id = "U<pk>".
    """
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                "employee_id": f"U{instance.pk}",
                "role": Role.EMPLOYEE,
            },
        )
