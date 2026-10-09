from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from incidents.models import Incident
from logs.models import LogEntry, PipelineRun


class SummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        entries = LogEntry.objects.filter(user=request.user)
        incidents = Incident.objects.filter(user=request.user)
        return Response({
            "total_logs": entries.count(),
            "error_count": entries.filter(level__in=["ERROR", "CRITICAL"]).count(),
            "warning_count": entries.filter(level="WARNING").count(),
            "incidents_total": incidents.count(),
            "open_incidents": incidents.filter(status="open").count(),
            "critical_incidents": incidents.filter(severity="critical").count(),
            "pipeline_runs": PipelineRun.objects.filter(user=request.user).count(),
        })


class ErrorTrendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = LogEntry.objects.filter(user=request.user)
        points = []
        for day in range(7):
            date = timezone.now().date() - timedelta(days=6 - day)
            count = qs.filter(timestamp__date=date).count()
            points.append({"date": date.isoformat(), "count": count})
        return Response({"results": points})


class ServicesSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = LogEntry.objects.filter(user=request.user).values("service_name").annotate(total=Count("id"), errors=Count("id", filter=Q(level__in=["ERROR", "CRITICAL"])))
        return Response({"results": list(qs.order_by("-total")[:10])})
