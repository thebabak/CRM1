from django.urls import path
from . import views

urlpatterns = [
    path("convert-to-persian/", views.convert_to_persian, name="convert_to_persian"),
    path("convert-to-persian/", views.convert_to_persian, name="convert_to_persian"),
    path("", views.request_list, name="home"),

    path("requests/", views.request_list, name="request_list"),
    path("requests/export/excel/", views.request_export_excel, name="request_export_excel"),

    path("requests/new/", views.request_create, name="request_create"),
    path("requests/new/hub/", views.new_request_hub, name="request_new_hub"),

    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/submit/", views.request_submit, name="request_submit"),
    path("requests/<int:pk>/approve/", views.request_approve, name="request_approve"),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
    path("requests/<int:pk>/cancel/", views.request_cancel, name="request_cancel"),

    path("leave/new/", views.leave_new, name="leave_new"),
    path("leave/<int:pk>/", views.leave_detail, name="leave_detail"),

    path("logout/", views.logout_page, name="logout"),

    # Profile Page
    path("profile/<int:user_id>/", views.profile_detail, name="profile_detail"),
]
