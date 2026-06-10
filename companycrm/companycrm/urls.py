from django.contrib import admin
from django.urls import path, include
from core.views import logout_page

from django.views.generic import RedirectView, TemplateView
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/logout/", logout_page, name="logout"),  # override built-in
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls")),
    path("accounts/profile/", RedirectView.as_view(pattern_name="home", permanent=False)),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_txt",)

]


