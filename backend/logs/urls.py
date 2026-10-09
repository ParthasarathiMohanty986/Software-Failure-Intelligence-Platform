from django.urls import path

from .views import LogDetailView, LogIngestView, LogListView, LogUploadView, PipelineRunDetailView, PipelineRunListView

urlpatterns = [
    path("upload/", LogUploadView.as_view(), name="logs-upload"),
    path("ingest/", LogIngestView.as_view(), name="logs-ingest"),
    path("", LogListView.as_view(), name="logs-list"),
    path("<int:pk>/", LogDetailView.as_view(), name="logs-detail"),
    path("pipeline-runs/", PipelineRunListView.as_view(), name="pipeline-runs-list"),
    path("pipeline-runs/<int:pk>/", PipelineRunDetailView.as_view(), name="pipeline-runs-detail"),
]
