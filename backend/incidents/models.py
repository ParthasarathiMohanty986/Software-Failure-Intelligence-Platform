from django.conf import settings
from django.db import models

from logs.models import LogEntry


class Incident(models.Model):
    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("investigating", "Investigating"),
        ("resolved", "Resolved"),
        ("ignored", "Ignored"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incidents")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    service_name = models.CharField(max_length=150, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open", db_index=True)
    error_signature = models.CharField(max_length=255, db_index=True)
    first_seen = models.DateTimeField(db_index=True)
    last_seen = models.DateTimeField(db_index=True)
    error_count = models.PositiveIntegerField(default=0)
    investigation_history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]
        indexes = [models.Index(fields=["user", "status", "severity"]), models.Index(fields=["user", "service_name", "first_seen"]) ]


class IncidentLog(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="incident_logs")
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name="incident_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("incident", "log_entry")
        indexes = [models.Index(fields=["incident", "created_at"])]

    def __str__(self):
        return f"{self.incident.title} -> {self.log_entry.id}"
