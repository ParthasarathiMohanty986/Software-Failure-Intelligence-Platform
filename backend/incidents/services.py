import re
from collections import defaultdict

from django.utils import timezone

from logs.models import LogEntry

from .models import Incident, IncidentLog


def _signature_for_log(log: LogEntry) -> str:
    message = re.sub(r"\b\d+\b", "#", (log.message or "")[:180])
    return f"{log.service_name}:{log.exception_type or 'generic'}:{message}"


def auto_group_errors(user, threshold: int = 3):
    grouped = defaultdict(list)
    for log in LogEntry.objects.filter(user=user, level__in=["ERROR", "CRITICAL"]).order_by("timestamp"):
        grouped[_signature_for_log(log)].append(log)

    created = 0
    for signature, entries in grouped.items():
        if len(entries) < threshold:
            continue
        group = sorted(entries, key=lambda item: item.timestamp)
        service_name = group[0].service_name
        severity = "low"
        if any(item.level == "CRITICAL" for item in group):
            severity = "critical"
        elif len(group) >= 10:
            severity = "high"
        elif len(group) >= 5:
            severity = "medium"

        incident, _ = Incident.objects.get_or_create(
            user=user,
            error_signature=signature[:255],
            defaults={
                "title": f"Recurring failure in {service_name}",
                "description": "Recurring service errors detected from log clustering.",
                "service_name": service_name,
                "severity": severity,
                "status": "open",
                "first_seen": group[0].timestamp,
                "last_seen": group[-1].timestamp,
                "error_count": len(group),
            },
        )
        if incident.first_seen > group[0].timestamp:
            incident.first_seen = group[0].timestamp
        if incident.last_seen < group[-1].timestamp:
            incident.last_seen = group[-1].timestamp
        incident.error_count = len(group)
        incident.severity = severity
        incident.title = f"Recurring {group[0].exception_type or 'error'} on {service_name}"
        incident.description = f"{len(group)} related {group[0].level.lower()} observations detected for {service_name}."
        incident.save(update_fields=["title", "description", "severity", "first_seen", "last_seen", "error_count"])

        for log in group:
            IncidentLog.objects.get_or_create(incident=incident, log_entry=log)
        created += 1
    return created
