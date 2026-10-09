from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from agents.runner import IncidentAgent
from investigations.models import Investigation
from logs.models import LogEntry

from .models import Incident, IncidentLog
from .services import auto_group_errors


class IncidentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Incident.objects.filter(user=request.user)
        service = request.query_params.get("service")
        status = request.query_params.get("status")
        severity = request.query_params.get("severity")
        query = request.query_params.get("q")
        if service:
            qs = qs.filter(service_name__icontains=service)
        if status:
            qs = qs.filter(status=status)
        if severity:
            qs = qs.filter(severity__iexact=severity)
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(error_signature__icontains=query))
        return Response({"results": [{
            "id": item.id,
            "title": item.title,
            "service_name": item.service_name,
            "severity": item.severity,
            "status": item.status,
            "error_signature": item.error_signature,
            "error_count": item.error_count,
            "last_seen": item.last_seen.isoformat(),
        } for item in qs[:50]]})


class IncidentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        incident = Incident.objects.filter(user=request.user, id=pk).first()
        if not incident:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "service_name": incident.service_name,
            "severity": incident.severity,
            "status": incident.status,
            "error_signature": incident.error_signature,
            "first_seen": incident.first_seen.isoformat(),
            "last_seen": incident.last_seen.isoformat(),
            "error_count": incident.error_count,
            "investigation_history": incident.investigation_history,
        })


class IncidentPatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        incident = Incident.objects.filter(user=request.user, id=pk).first()
        if not incident:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        allowed = ["severity", "status", "title", "description"]
        for key in allowed:
            if key in request.data:
                setattr(incident, key, request.data[key])
        incident.save()
        return Response({"status": "updated", "incident_id": incident.id})


class IncidentLogsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        incident = Incident.objects.filter(user=request.user, id=pk).first()
        if not incident:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        linked = IncidentLog.objects.filter(incident=incident).select_related("log_entry")
        entries = [item.log_entry for item in linked.order_by("-log_entry__timestamp")[:50]]
        return Response({"results": [{
            "id": item.id,
            "service_name": item.service_name,
            "level": item.level,
            "message": item.message,
            "timestamp": item.timestamp.isoformat(),
            "exception_type": item.exception_type,
        } for item in entries]})


class TriggerInvestigationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        incident = Incident.objects.filter(user=request.user, id=pk).first()
        if not incident:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        investigation = IncidentAgent(incident, request.user).run()
        return Response({"investigation_id": investigation.id, "status": investigation.status})


class GroupIncidentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        created = auto_group_errors(request.user)
        return Response({"created": created})
