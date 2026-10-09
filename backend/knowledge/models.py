from django.conf import settings
from django.db import models


class KnowledgeDocument(models.Model):
    DOCUMENT_TYPES = [("markdown", "Markdown"), ("text", "Text"), ("pdf", "PDF")]
    STATUS_CHOICES = [("pending", "Pending"), ("indexed", "Indexed"), ("failed", "Failed")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="knowledge_documents")
    title = models.CharField(max_length=255)
    file_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES, default="text")
    content = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    indexed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class DocumentChunk(models.Model):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField(default=0)
    content = models.TextField()
    embedding = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
