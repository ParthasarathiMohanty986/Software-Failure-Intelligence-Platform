from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/logs/", include("logs.urls")),
    path("api/incidents/", include("incidents.urls")),
    path("api/investigations/", include("investigations.urls")),
    path("api/knowledge/", include("knowledge.urls")),
    path("api/analytics/", include("analytics.urls")),
]
