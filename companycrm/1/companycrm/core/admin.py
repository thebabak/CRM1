# core/admin.py
from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Department,
    Position,
    Profile,
    Role,
    Request,
    RequestStatus,
    Approval,
    LeaveRequest,
    LeaveBalanceAdjustment,
    leave_year_stats,
)


# ─────────────── Simple lookups ───────────────

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ─────────────── Adjustments (standalone admin) ───────────────

@admin.register(LeaveBalanceAdjustment)
class LeaveBalanceAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("user_display", "year", "delta_days", "reason", "created_by", "created_at")
    list_filter = ("year",)
    search_fields = (
        "user_profile__user__username",
        "user_profile__user__first_name",
        "user_profile__user__last_name",
        "reason",
    )
    ordering = ("-created_at",)
    autocomplete_fields = ("user_profile", "created_by")

    readonly_fields = (
        "created_at",
        "preview_year",
        "preview_accrued",
        "preview_used",
        "preview_remaining",
    )

    fieldsets = (
        (None, {"fields": ("user_profile", "year", "delta_days", "reason")}),
        ("Audit", {"fields": ("created_by", "created_at")}),
        ("Preview (current-year quick view)", {
            "description": "Shows the user's current-year balance (not necessarily this adjustment year).",
            "fields": ("preview_year", "preview_accrued", "preview_used", "preview_remaining"),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # Display helpers
    def user_display(self, obj):
        u = obj.user_profile.user
        return u.get_full_name() or u.username
    user_display.short_description = "User"

    # Balance preview helpers (current year)
    def _stats(self, obj):
        try:
            return leave_year_stats(obj.user_profile.user)
        except Exception:
            return {"year": "", "accrued": "", "used": "", "remaining": ""}

    def preview_year(self, obj): return self._stats(obj)["year"]
    def preview_accrued(self, obj): return self._stats(obj)["accrued"]
    def preview_used(self, obj): return self._stats(obj)["used"]
    def preview_remaining(self, obj): return self._stats(obj)["remaining"]


# ─────────────── Inline on Profile ───────────────

class LeaveBalanceAdjustmentInline(admin.TabularInline):
    model = LeaveBalanceAdjustment
    extra = 0
    autocomplete_fields = ("created_by",)
    fields = ("year", "delta_days", "reason", "created_by", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_id", "role", "position_display", "departments_list")
    list_filter = ("role", "departments", "position")
    search_fields = ("user__username", "user__first_name", "user__last_name", "employee_id")
    autocomplete_fields = ("user", "position")
    inlines = [LeaveBalanceAdjustmentInline]

    def position_display(self, obj):
        return getattr(obj.position, "name", "")
    position_display.short_description = "Position"

    def departments_list(self, obj):
        return ", ".join(obj.departments.values_list("name", flat=True))


# ─────────────── Requests & Approvals ───────────────

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "created_by",
        "status",
        "required_user",
        "required_role_display",
        "created_at",
    )
    list_filter = ("status", "required_role", "created_at")
    search_fields = ("title", "body", "created_by__username")
    autocomplete_fields = ("created_by", "required_user")
    date_hierarchy = "created_at"

    def required_role_display(self, obj):
        return dict(Role.choices).get(obj.required_role, obj.required_role)
    required_role_display.short_description = "Required Role"


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "request", "decided_by", "get_decided_role", "decision", "decided_at")
    list_filter = ("decision", "decided_role", "decided_at")
    search_fields = ("request__title", "decided_by__username", "comment")
    autocomplete_fields = ("request", "decided_by")
    date_hierarchy = "decided_at"

    def get_decided_role(self, obj):
        return dict(Role.choices).get(obj.decided_role, obj.decided_role)
    get_decided_role.short_description = "Role"


# ─────────────── Leave requests (DAYS + BALANCE) ───────────────

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    """
    Shows requested days (computed) and live current-year balance for the creator.
    """
    list_display = (
        "id",
        "employee",                # creator (from base request)
        "leave_type",
        "mode",
        "when_display",
        "requested_days_display",  # computed
        "status",
        "replacement",
        "created_at",
    )
    list_filter = (
        "leave_type",
        "mode",
        "created_at",
        ("base_request__status", admin.ChoicesFieldListFilter),
    )
    search_fields = (
        "base_request__title",
        "base_request__created_by__username",
        "full_name",
        "personnel_code",
    )
    autocomplete_fields = ("base_request", "replacement")
    date_hierarchy = "created_at"

    readonly_fields = (
        # Linked/meta
        "employee",
        "status",
        # Computed
        "requested_days_display",
        # Live balance (current year)
        "balance_year",
        "balance_accrued",
        "balance_used",
        "balance_remaining",
    )

    fieldsets = (
        ("Linked Request", {"fields": ("base_request", "employee", "status")}),
        ("Employee Snapshot", {"fields": ("full_name", "position", "personnel_code")}),
        ("Leave Details", {"fields": ("leave_type", "mode")}),
        ("Daily", {"fields": ("daily_from", "daily_to", "duration_days")}),
        ("Hourly", {"fields": ("hourly_date", "hourly_from", "hourly_to")}),
        ("Replacement", {"fields": ("replacement",)}),
        ("Computed", {"fields": ("requested_days_display",)}),
        ("Current-Year Balance (Live)", {
            "description": "Accrual: 2.5 days/month, capped at 30 days/year (plus admin adjustments).",
            "fields": ("balance_year", "balance_accrued", "balance_used", "balance_remaining"),
        }),
    )

    # ---------- list columns ----------

    def employee(self, obj: LeaveRequest):
        u = obj.base_request.created_by
        return u.get_full_name() or u.username
    employee.short_description = "Employee"
    employee.admin_order_field = "base_request__created_by__username"

    def status(self, obj: LeaveRequest):
        return obj.base_request.status
    status.admin_order_field = "base_request__status"

    def when_display(self, obj: LeaveRequest):
        if obj.mode == "DAILY":
            if obj.daily_from and obj.daily_to:
                return f"{obj.daily_from} → {obj.daily_to}"
            return "—"
        if obj.mode == "HOURLY":
            if obj.hourly_date and obj.hourly_from and obj.hourly_to:
                return f"{obj.hourly_date} {obj.hourly_from}–{obj.hourly_to}"
            return "—"
        return "—"
    when_display.short_description = "When"

    def requested_days_display(self, obj: LeaveRequest):
        d = obj.requested_days()
        if d == 0:
            return format_html('<span style="color:#888">0.00</span>')
        return f"{d:.2f}"
    requested_days_display.short_description = "Requested Days"

    # ---------- readonly balance fields ----------

    def _stats(self, obj: LeaveRequest):
        return leave_year_stats(obj.base_request.created_by)

    def balance_year(self, obj: LeaveRequest):
        return self._stats(obj)["year"]

    def balance_accrued(self, obj: LeaveRequest):
        return self._stats(obj)["accrued"]

    def balance_used(self, obj: LeaveRequest):
        return self._stats(obj)["used"]

    def balance_remaining(self, obj: LeaveRequest):
        return self._stats(obj)["remaining"]
