from django.conf import settings
from django.db import models


class PipelineRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pipeline_runs")
    source_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_records = models.PositiveIntegerField(default=0)
    accepted_records = models.PositiveIntegerField(default=0)
    rejected_records = models.PositiveIntegerField(default=0)
    duplicate_records = models.PositiveIntegerField(default=0)
    skipped_records = models.PositiveIntegerField(default=0)
    processing_duration_ms = models.IntegerField(default=0)
    error_details = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status", "created_at"]) ]


class LogEntry(models.Model):
    LOG_LEVELS = [
        ("DEBUG", "Debug"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="log_entries")
    timestamp = models.DateTimeField(db_index=True)
    service_name = models.CharField(max_length=150, db_index=True)
    level = models.CharField(max_length=20, choices=LOG_LEVELS, default="INFO", db_index=True)
    message = models.TextField()
    environment = models.CharField(max_length=100, default="production", db_index=True)
    status_code = models.IntegerField(null=True, blank=True, db_index=True)
    trace_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    exception_type = models.CharField(max_length=255, blank=True, default="", db_index=True)
    stack_trace = models.TextField(blank=True, default="")
    fingerprint = models.CharField(max_length=128, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "fingerprint"], name="unique_user_log_fingerprint"),
        ]
        indexes = [
            models.Index(fields=["user", "service_name", "timestamp"]),
            models.Index(fields=["user", "level", "timestamp"]),
            models.Index(fields=["user", "exception_type", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.service_name} {self.level} {self.timestamp}"
