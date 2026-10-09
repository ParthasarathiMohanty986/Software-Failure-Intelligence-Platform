from django.conf import settings
from django.db import models

from incidents.models import Incident


class Investigation(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="investigations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="investigations")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    summary = models.TextField(blank=True, default="")
    result = models.JSONField(default=dict, blank=True)
    tool_history = models.JSONField(default=list, blank=True)
    evidence = models.JSONField(default=dict, blank=True)
    provider = models.CharField(max_length=50, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    execution_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class InvestigationEvent(models.Model):
    investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=50)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
