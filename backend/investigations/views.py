from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from investigations.models import Investigation, InvestigationEvent


class InvestigationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Investigation.objects.filter(user=request.user)
        return Response({"results": [{
            "id": item.id,
            "incident_id": item.incident_id,
            "summary": item.summary,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
        } for item in qs[:50]]})


class InvestigationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        item = Investigation.objects.filter(user=request.user, id=pk).first()
        if not item:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": item.id,
            "incident_id": item.incident_id,
            "status": item.status,
            "summary": item.summary,
            "result": item.result,
            "evidence": item.evidence,
            "tool_history": item.tool_history,
            "provider": item.provider,
            "created_at": item.created_at.isoformat(),
        })


class InvestigationEventListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        investigation = Investigation.objects.filter(user=request.user, id=pk).first()
        if not investigation:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"results": [{
            "id": event.id,
            "event_type": event.event_type,
            "details": event.details,
            "created_at": event.created_at.isoformat(),
        } for event in investigation.events.all()]})
