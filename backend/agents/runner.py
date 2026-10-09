from __future__ import annotations

from typing import Any

from django.conf import settings

from incidents.models import Incident
from investigations.models import Investigation, InvestigationEvent

from .tools import (
    get_error_frequency,
    get_pipeline_health,
    get_recent_errors,
    get_related_logs,
    get_service_error_summary,
    search_runbooks,
)


class IncidentAgent:
    def __init__(self, incident: Incident, user, max_steps: int | None = None):
        self.incident = incident
        self.user = user
        self.max_steps = max_steps or getattr(settings, "APP_CONFIG", {}).get("agent_max_steps", 4)

    def run(self):
        investigation = Investigation.objects.create(
            incident=self.incident,
            user=self.user,
            status="running",
            provider="langchain",
        )
        InvestigationEvent.objects.create(investigation=investigation, event_type="start", details={"service": self.incident.service_name})

        evidence = {}
        tool_history = []
        for step in range(self.max_steps):
            if step == 0:
                tool_history.append({"step": step + 1, "tool": "get_recent_errors", "args": {"service_name": self.incident.service_name, "time_window": "24h"}})
                evidence["recent_errors"] = get_recent_errors.invoke({"service_name": self.incident.service_name, "time_window": "24h"})
            if step == 1:
                tool_history.append({"step": step + 1, "tool": "get_error_frequency", "args": {"error_signature": self.incident.error_signature, "time_window": "7d"}})
                evidence["frequency"] = get_error_frequency.invoke({"error_signature": self.incident.error_signature, "time_window": "7d"})
            if step == 2:
                tool_history.append({"step": step + 1, "tool": "get_related_logs", "args": {"incident_id": self.incident.id, "limit": 20}})
                evidence["related_logs"] = get_related_logs.invoke({"incident_id": self.incident.id, "limit": 20})
            if step == 3:
                tool_history.append({"step": step + 1, "tool": "search_runbooks", "args": {"query": self.incident.service_name + " " + self.incident.error_signature}})
                evidence["runbooks"] = search_runbooks.invoke({"query": self.incident.service_name + " " + self.incident.error_signature})
            if step == 4:
                tool_history.append({"step": step + 1, "tool": "get_pipeline_health", "args": {}})
                evidence["pipeline_health"] = get_pipeline_health.invoke({})
                break

            InvestigationEvent.objects.create(investigation=investigation, event_type="tool_call", details={"step": step + 1, "tool": tool_history[-1]})

        summary = {
            "incident_id": self.incident.id,
            "service": self.incident.service_name,
            "status": "completed",
            "tool_history": tool_history,
            "evidence": evidence,
        }
        investigation.status = "completed"
        investigation.summary = "Reviewed recent failures and supporting telemetry for the incident."
        investigation.result = summary
        investigation.evidence = evidence
        investigation.tool_history = tool_history
        investigation.save()
        InvestigationEvent.objects.create(investigation=investigation, event_type="complete", details={"summary": summary})
        return investigation
