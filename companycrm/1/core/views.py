# core/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RequestForm, LeaveRequestForm  # and RequestActionForm if you use it
from .models import (
    Request,
    RequestStatus,
    Decision,
    apply_decision,
    can_user_approve,
    leave_year_stats,
)

# Optional registry for the "New Request" hub
try:
    from .forms_registry import FORMS
except Exception:
    FORMS = []


# =========================
# Requests (generic)
# =========================
@login_required
def request_list(request):
    qs = Request.objects.all().select_related("created_by__profile")
    if request.GET.get("mine") == "1":
        qs = qs.filter(created_by=request.user)
    if request.GET.get("pending") == "1":
        qs = qs.exclude(status__in=[RequestStatus.APPROVED, RequestStatus.REJECTED])
    return render(request, "core/request_list.html", {"requests": qs})


@login_required
def request_create(request):
    if request.method == "POST":
        form = RequestForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.status = RequestStatus.DRAFT
            obj.save()
            messages.success(request, "Draft created.")
            return redirect("request_detail", pk=obj.pk)
    else:
        form = RequestForm()
    return render(request, "core/request_form.html", {"form": form})


@login_required
def request_detail(request, pk):
    obj = get_object_or_404(
        Request.objects.select_related("created_by__profile").prefetch_related("approvals"),
        pk=pk,
    )
    can_act = (not obj.is_terminal()) and can_user_approve(request.user, obj)
    # Show live balance if this request is a leave
    stats = leave_year_stats(request.user) if hasattr(obj, "leave") else None
    return render(request, "core/request_detail.html", {"obj": obj, "can_act": can_act, "stats": stats})


@login_required
@require_POST
def request_submit(request, pk):
    obj = get_object_or_404(Request, pk=pk, created_by=request.user)
    if obj.status != RequestStatus.DRAFT:
        messages.info(request, "Only drafts can be submitted.")
        return redirect("request_detail", pk=obj.pk)
    obj.submit()
    messages.success(request, "Request submitted for approval.")
    return redirect("request_detail", pk=obj.pk)


@login_required
@require_POST
def request_approve(request, pk):
    obj = get_object_or_404(Request, pk=pk)
    if not can_user_approve(request.user, obj):
        return HttpResponseForbidden("Not allowed")
    apply_decision(request.user, obj, Decision.APPROVE, comment=request.POST.get("comment", ""))
    messages.success(request, "Approved.")
    return redirect("request_detail", pk=obj.pk)


@login_required
@require_POST
def request_reject(request, pk):
    obj = get_object_or_404(Request, pk=pk)
    if not can_user_approve(request.user, obj):
        return HttpResponseForbidden("Not allowed")
    apply_decision(request.user, obj, Decision.REJECT, comment=request.POST.get("comment", ""))
    messages.warning(request, "Rejected.")
    return redirect("request_detail", pk=obj.pk)


# =========================
# Leave (typed request)
# =========================
@login_required
def leave_new(request):
    """
    Create the typed LeaveRequest first (so replacement is known),
    then call base.submit() which sets the first approver (replacement if provided).
    Also show the user's current-year leave balance.
    """
    stats = leave_year_stats(request.user)
    if request.method == "POST":
        form = LeaveRequestForm(request.POST, request=request)  # pass request for filtering replacement queryset
        if form.is_valid():
            with transaction.atomic():
                base = Request.objects.create(
                    title=f"Leave Request - {request.user.get_username()}",
                    body="Leave request submitted via form",
                    created_by=request.user,
                    status=RequestStatus.DRAFT,
                )
                leave = form.save(commit=False)
                if not leave.full_name:
                    leave.full_name = request.user.get_full_name() or request.user.get_username()
                leave.base_request = base
                leave.save()
                base.submit()
                messages.success(request, "Leave request submitted.")
                return redirect("request_detail", pk=base.pk)
    else:
        initial = {"full_name": request.user.get_full_name() or request.user.get_username()}
        form = LeaveRequestForm(initial=initial, request=request)
    return render(request, "core/leave_form.html", {"form": form, "stats": stats})


@login_required
def leave_detail(request, pk):
    base = get_object_or_404(Request, pk=pk)
    leave = getattr(base, "leave", None)
    stats = leave_year_stats(request.user)
    return render(request, "core/leave_detail.html", {"obj": base, "leave": leave, "stats": stats})


# =========================
# New Request hub
# =========================
@login_required
def new_request_hub(request):
    return render(request, "core/request_new_hub.html", {"forms_list": FORMS})


# =========================
# Logout (GET confirm + POST)
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def logout_page(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return render(request, "registration/logout.html")
