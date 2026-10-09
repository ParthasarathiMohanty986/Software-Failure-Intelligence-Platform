from django.urls import path

from .views import ErrorTrendView, ServicesSummaryView, SummaryView

urlpatterns = [
    path("summary/", SummaryView.as_view(), name="analytics-summary"),
    path("errors-over-time/", ErrorTrendView.as_view(), name="analytics-trends"),
    path("services/", ServicesSummaryView.as_view(), name="analytics-services"),
]
