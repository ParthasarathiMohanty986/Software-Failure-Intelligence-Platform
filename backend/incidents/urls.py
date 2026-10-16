from django.urls import path

from .views import IncidentDetailView, IncidentListView, IncidentLogsView, IncidentPatchView, TriggerInvestigationView, GroupIncidentsView

urlpatterns = [
    path("detect/", GroupIncidentsView.as_view()),
    path("", IncidentListView.as_view(), name="incidents-list"),
    path("<int:pk>/", IncidentDetailView.as_view(), name="incidents-detail"),
    path("<int:pk>/logs/", IncidentLogsView.as_view(), name="incidents-logs"),
    path("<int:pk>/investigate/", TriggerInvestigationView.as_view(), name="incidents-investigate"),
    path("<int:pk>/update/", IncidentPatchView.as_view(), name="incidents-patch"),
]
