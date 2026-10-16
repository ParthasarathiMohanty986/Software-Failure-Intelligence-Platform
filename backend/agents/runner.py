from datetime import timedelta
from time import monotonic

from django.conf import settings
from django.utils import timezone

from ai.services import generate_incident_analysis
from investigations.models import Investigation, InvestigationEvent
from knowledge.services import search_user_runbooks
from logs.models import LogEntry


class IncidentAgent:
    def __init__(self, incident, user, max_steps=None):
        self.incident = incident
        self.user = user

    def run(self):
        if self.incident.user_id != self.user.id:
            raise PermissionError("Incident does not belong to this user")
        started = monotonic()
        investigation = Investigation.objects.create(
            incident=self.incident, user=self.user, status="running",
            provider=settings.APP_CONFIG["ai_model"],
        )
        self.incident.status = "investigating"
        self.incident.save(update_fields=["status"])
        evidence = {}
        history = []

        def record(name, value):
            evidence[name] = value
            history.append({"step": len(history) + 1, "tool": name})
            InvestigationEvent.objects.create(investigation=investigation, event_type="tool_call", details=history[-1])

        def serialize(qs):
            return [{"id": log.id, "service": log.service_name, "level": log.level,
                     "message": log.message, "timestamp": log.timestamp.isoformat(),
                     "exception_type": log.exception_type} for log in qs]

        InvestigationEvent.objects.create(investigation=investigation, event_type="start", details={})
        try:
            owned = LogEntry.objects.filter(user=self.user)
            related = owned.filter(incident_links__incident=self.incident)
            record("related_logs", serialize(related.order_by("-timestamp")[:20]))
            record("recent_errors", serialize(owned.filter(
                service_name=self.incident.service_name, level__in=["ERROR", "CRITICAL"],
                timestamp__gte=timezone.now() - timedelta(hours=24)).order_by("-timestamp")[:10]))
            record("frequency", {"count": related.filter(timestamp__gte=timezone.now() - timedelta(days=7)).count(),
                                 "time_window": "7d", "total_linked_logs": related.count()})
            record("runbooks", search_user_runbooks(self.user, self.incident.service_name + " " + self.incident.error_signature))
            analysis = generate_incident_analysis(
                {"id": self.incident.id, "service": self.incident.service_name,
                 "signature": self.incident.error_signature, "severity": self.incident.severity,
                 "error_count": self.incident.error_count},
                evidence["related_logs"], evidence["frequency"], evidence["runbooks"],
            )
            investigation.result = analysis.model_dump()
            investigation.summary = analysis.executive_summary
            investigation.status = "completed"
        except Exception as exc:
            # Do not persist provider exception text, which can include credentials or request data.
            investigation.status = "failed"
            investigation.error_message = "AI investigation unavailable (" + type(exc).__name__ + "). Check the configured provider API key, AI_MODEL, provider quota and connectivity, then retry."
            investigation.summary = "Investigation incomplete. Collected evidence is available below; no AI diagnosis was produced."
        investigation.evidence = evidence
        investigation.tool_history = history
        investigation.execution_time_ms = int((monotonic() - started) * 1000)
        investigation.save()
        InvestigationEvent.objects.create(investigation=investigation, event_type=investigation.status, details={"error": investigation.error_message})
        return investigation
