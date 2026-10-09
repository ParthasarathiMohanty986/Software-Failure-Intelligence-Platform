from django.urls import path

from .views import InvestigationDetailView, InvestigationEventListView, InvestigationListView

urlpatterns = [
    path("", InvestigationListView.as_view(), name="investigations-list"),
    path("<int:pk>/", InvestigationDetailView.as_view(), name="investigations-detail"),
    path("<int:pk>/events/", InvestigationEventListView.as_view(), name="investigations-events"),
]
