from datetime import datetime, timedelta
from typing import Any

from django.db.models import Count, Q
from langchain_core.tools import tool

from incidents.models import Incident
from knowledge.services import search_user_runbooks
from logs.models import LogEntry, PipelineRun


@tool
def get_recent_errors(service_name: str, time_window: str = "24h") -> str:
    """Retrieve recent errors for a service."""
    service_name = (service_name or "").strip()
    if not service_name:
        raise ValueError("service_name is required")

    delta = parse_time_window(time_window)
    qs = LogEntry.objects.filter(service_name__icontains=service_name, timestamp__gte=datetime.utcnow() - delta, level__in=["ERROR", "CRITICAL"])[:10]
    return str([
        {"id": item.id, "message": item.message, "timestamp": item.timestamp.isoformat(), "exception_type": item.exception_type}
        for item in qs
    ])


@tool
def get_error_frequency(error_signature: str, time_window: str = "7d") -> str:
    """Calculate error frequency for an error signature over time."""
    if not error_signature:
        raise ValueError("error_signature is required")
    qs = LogEntry.objects.filter(exception_type__icontains=error_signature, timestamp__gte=datetime.utcnow() - parse_time_window(time_window))
    return str({"count": qs.count(), "signature": error_signature})


@tool
def get_related_logs(incident_id: int, limit: int = 20) -> str:
    """Retrieve logs for an incident."""
    incident = Incident.objects.filter(id=incident_id).first()
    if not incident:
        raise ValueError("incident not found")
    logs = LogEntry.objects.filter(incident_links__incident=incident).order_by("-timestamp")[:limit]
    return str([
        {"id": item.id, "service_name": item.service_name, "message": item.message, "exception_type": item.exception_type, "timestamp": item.timestamp.isoformat()}
        for item in logs
    ])


@tool
def get_service_error_summary(service_name: str, time_window: str = "7d") -> str:
    """Summarize severity counts and common signatures for a service."""
    delta = parse_time_window(time_window)
    qs = LogEntry.objects.filter(service_name__icontains=service_name, timestamp__gte=datetime.utcnow() - delta)
    counts = qs.values("level").annotate(total=Count("id")).order_by("-total")
    signatures = qs.exclude(exception_type="").values("exception_type").annotate(total=Count("id")).order_by("-total")[:5]
    return str({"counts": list(counts), "signatures": list(signatures)})


@tool
def search_runbooks(query: str, user_id: int) -> str:
    """Find relevant troubleshooting documentation."""
    if not query:
        return "[]"
    return str(search_user_runbooks(user_id, query, limit=5))


@tool
def get_pipeline_health() -> str:
    """Inspect recent pipeline runs and failures."""
    runs = PipelineRun.objects.order_by("-created_at")[:10]
    summary = {"runs": [{
        "id": r.id,
        "status": r.status,
        "source_name": r.source_name,
        "accepted": r.accepted_records,
        "rejected": r.rejected_records,
        "duplicates": r.duplicate_records,
    } for r in runs]}
    return str(summary)


def parse_time_window(time_window: str) -> timedelta:
    if time_window is None:
        return timedelta(days=1)
    value = str(time_window).strip().lower()
    if value.endswith("h"):
        return timedelta(hours=int(value[:-1]))
    if value.endswith("d"):
        return timedelta(days=int(value[:-1]))
    if value.endswith("w"):
        return timedelta(weeks=int(value[:-1]))
    return timedelta(days=1)
