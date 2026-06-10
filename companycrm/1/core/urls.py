from django.urls import path
from . import views
from django.views.generic import RedirectView


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="request_new_hub", permanent=False), name="home"),
    path("requests/", views.request_list, name="request_list"),

    # NEW: hub that lists all available request forms
    path("requests/new/", views.new_request_hub, name="request_new_hub"),

    # Keep your generic text request (optional, different route now)
    path("requests/new/freeform/", views.request_create, name="request_create"),

    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/submit/", views.request_submit, name="request_submit"),
    path("requests/<int:pk>/approve/", views.request_approve, name="request_approve"),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),

    # Leave form already built
    path("leave/new/", views.leave_new, name="leave_new"),
    path("leave/<int:pk>/", views.leave_detail, name="leave_detail"),
    # core/urls.py

    # Actions
    path("requests/<int:pk>/approve/", views.request_approve, name="request_approve"),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
]