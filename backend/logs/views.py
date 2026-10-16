import json
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LogEntry, PipelineRun
from incidents.services import auto_group_errors
from .services import create_pipeline_run, get_rows_from_upload, ingest_records


class LogUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "A log file is required."}, status=status.HTTP_400_BAD_REQUEST)
        source_name = request.data.get("source_name") or getattr(file_obj, "name", "upload")
        try:
            rows = get_rows_from_upload(file_obj)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        pipeline = create_pipeline_run(request.user, source_name, len(rows))
        pipeline.status = "running"
        pipeline.save(update_fields=["status"])
        try:
            result = ingest_records(rows, request.user, source_name, pipeline=pipeline)
            pipeline.total_records = len(rows)
            pipeline.accepted_records = result["accepted"]
            pipeline.rejected_records = result["rejected"]
            pipeline.duplicate_records = result["duplicate"]
            pipeline.error_details = result["errors"]
            pipeline.status = "completed"
            pipeline.save()
            auto_group_errors(request.user)
            return Response({"pipeline_id": pipeline.id, "summary": result}, status=status.HTTP_200_OK)
        except Exception as exc:
            pipeline.status = "failed"
            pipeline.error_details = [{"detail": str(exc)}]
            pipeline.save(update_fields=["status", "error_details"])
            return Response({"detail": "Log ingestion failed", "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogIngestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        records = request.data.get("records") or request.data.get("logs") or []
        if not records:
            return Response({"detail": "No records provided."}, status=status.HTTP_400_BAD_REQUEST)
        pipeline = create_pipeline_run(request.user, "manual_ingest", len(records))
        pipeline.status = "running"
        pipeline.save(update_fields=["status"])
        result = ingest_records(records, request.user, "manual_ingest", pipeline=pipeline)
        pipeline.total_records = len(records)
        pipeline.accepted_records = result["accepted"]
        pipeline.rejected_records = result["rejected"]
        pipeline.duplicate_records = result["duplicate"]
        pipeline.error_details = result["errors"]
        pipeline.status = "completed"
        pipeline.save()
        auto_group_errors(request.user)
        return Response({"pipeline_id": pipeline.id, "summary": result})


class LogListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = LogEntry.objects.filter(user=request.user)
        service = request.query_params.get("service")
        level = request.query_params.get("level")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        q = request.query_params.get("q")

        if service:
            qs = qs.filter(service_name__icontains=service)
        if level:
            qs = qs.filter(level__iexact=level)
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)
        if q:
            qs = qs.filter(Q(message__icontains=q) | Q(exception_type__icontains=q))

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start_index = (page - 1) * page_size
        total = qs.count()
        items = qs[start_index:start_index + page_size]
        return Response({"count": total, "results": [{
            "id": item.id,
            "service_name": item.service_name,
            "level": item.level,
            "message": item.message,
            "timestamp": item.timestamp.isoformat(),
            "exception_type": item.exception_type,
            "status_code": item.status_code,
            "trace_id": item.trace_id,
        } for item in items]})


class LogDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        item = LogEntry.objects.filter(user=request.user, id=pk).first()
        if not item:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": item.id,
            "timestamp": item.timestamp.isoformat(),
            "service_name": item.service_name,
            "level": item.level,
            "message": item.message,
            "environment": item.environment,
            "status_code": item.status_code,
            "trace_id": item.trace_id,
            "exception_type": item.exception_type,
            "stack_trace": item.stack_trace,
            "raw_payload": item.raw_payload,
        })


class PipelineRunListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = PipelineRun.objects.filter(user=request.user)
        return Response({"results": [{
            "id": item.id,
            "source_name": item.source_name,
            "status": item.status,
            "total_records": item.total_records,
            "accepted_records": item.accepted_records,
            "rejected_records": item.rejected_records,
            "duplicate_records": item.duplicate_records,
            "created_at": item.created_at.isoformat(),
        } for item in qs[:50]]})


class PipelineRunDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        item = PipelineRun.objects.filter(user=request.user, id=pk).first()
        if not item:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": item.id,
            "source_name": item.source_name,
            "status": item.status,
            "total_records": item.total_records,
            "accepted_records": item.accepted_records,
            "rejected_records": item.rejected_records,
            "duplicate_records": item.duplicate_records,
            "error_details": item.error_details,
            "created_at": item.created_at.isoformat(),
            "started_at": item.started_at.isoformat() if item.started_at else None,
            "finished_at": item.finished_at.isoformat() if item.finished_at else None,
        })
