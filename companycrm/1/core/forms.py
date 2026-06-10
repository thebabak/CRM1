# core/forms.py
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Count

from .models import Request, LeaveRequest, LeaveMode

User = get_user_model()

# Policy switch: also require replacement be in the same department(s) as requester
SAME_DEPARTMENT_ONLY = True


# ---------- Simple freeform Request form ----------
class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ["title", "body"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Subject / Title", "class": "form-control"}),
            "body": forms.Textarea(attrs={"rows": 6, "placeholder": "Describe the request", "class": "form-control"}),
        }


# ---------- Pretty labels for replacement dropdown ----------
class ReplacementChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        prof = getattr(obj, "profile", None)
        name = obj.get_full_name() or obj.get_username()
        if not prof:
            return name
        pos = getattr(prof.position, "name", None)
        deps = ", ".join(d.name for d in prof.departments.all())
        parts = [name]
        if pos:
            parts.append(pos)
        if deps:
            parts.append(deps)
        return " — ".join(parts)


# ---------- LeaveRequest form ----------
class LeaveRequestForm(forms.ModelForm):
    """
    Replacement rules:
      - must be ACTIVE user with a profile
      - must have EXACTLY ONE department
      - must be SAME ROLE (same layer) as the requester
      - (optional) must share a department with requester (SAME_DEPARTMENT_ONLY)
      - cannot be the requester themselves
    """
    replacement = ReplacementChoiceField(
        queryset=User.objects.none(),  # set in __init__
        required=False,
        help_text="Only peers with exactly one department are listed.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = LeaveRequest
        fields = [
            "position", "personnel_code", "full_name",
            "leave_type", "mode",
            "daily_from", "daily_to", "duration_days",
            "hourly_date", "hourly_from", "hourly_to",
            "replacement",
        ]
        widgets = {
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "personnel_code": forms.TextInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),

            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "mode": forms.Select(attrs={"class": "form-select"}),

            "daily_from": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "daily_to": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "duration_days": forms.NumberInput(attrs={"step": "0.5", "class": "form-control"}),

            "hourly_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "hourly_from": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "hourly_to": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        # `request` is injected by the view so we can filter replacement candidates
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        qs = (
            User.objects.filter(is_active=True, profile__isnull=False)
            .annotate(dep_count=Count("profile__departments"))
            .filter(dep_count=1)  # exactly one department
            .select_related("profile", "profile__position")
            .prefetch_related("profile__departments")
            .distinct()
        )

        if self.request and self.request.user.is_authenticated:
            req_user = self.request.user
            qs = qs.exclude(pk=req_user.pk)  # cannot select self

            # Same layer (same role as requester)
            req_prof = getattr(req_user, "profile", None)
            if req_prof:
                qs = qs.filter(profile__role=req_prof.role)

                # Optional: same department(s)
                if SAME_DEPARTMENT_ONLY:
                    req_deps = list(req_prof.departments.values_list("pk", flat=True))
                    if req_deps:
                        qs = qs.filter(profile__departments__in=req_deps)

        # Order for nicer UX
        qs = qs.order_by("profile__position__name", "first_name", "last_name", "username")
        self.fields["replacement"].queryset = qs
        self.fields["replacement"].label = "Replacement (peer)"

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("mode")

        # Mode-specific required fields
        if mode == LeaveMode.DAILY:
            if not cleaned.get("daily_from") or not cleaned.get("daily_to"):
                self.add_error("daily_from", "Required")
                self.add_error("daily_to", "Required")
        elif mode == LeaveMode.HOURLY:
            for f in ["hourly_date", "hourly_from", "hourly_to"]:
                if not cleaned.get(f):
                    self.add_error(f, "Required")

        # Defensive validation for replacement selection
        rep = cleaned.get("replacement")
        req_user = getattr(self.request, "user", None)
        req_prof = getattr(req_user, "profile", None) if req_user and req_user.is_authenticated else None

        if rep:
            rep_prof = getattr(rep, "profile", None)

            # must have profile & exactly one department
            if not rep_prof or rep_prof.departments.count() != 1:
                self.add_error("replacement", "Replacement must belong to exactly one department.")

            # same layer (same role)
            if req_prof and rep_prof and rep_prof.role != req_prof.role:
                self.add_error("replacement", "Replacement must be the same role level as the requester.")

            # optional: same department(s)
            if SAME_DEPARTMENT_ONLY and req_prof and rep_prof:
                req_deps = set(req_prof.departments.values_list("pk", flat=True))
                rep_deps = set(rep_prof.departments.values_list("pk", flat=True))
                if not (req_deps & rep_deps):
                    self.add_error("replacement", "Replacement must be in the same department as the requester.")

            # cannot be self
            if req_user and rep.pk == req_user.pk:
                self.add_error("replacement", "You cannot select yourself as the replacement.")

        return cleaned


# ---------- Approve/Reject small form (comment only) ----------
class RequestActionForm(forms.Form):
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Comment (optional)", "class": "form-control"}),
        label="",
    )
