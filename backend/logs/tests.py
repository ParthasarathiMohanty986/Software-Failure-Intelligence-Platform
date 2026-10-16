from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
import json
from pathlib import Path

from .models import LogEntry, PipelineRun


class LogUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(username="upload-test"))
        self.records = json.loads((Path(__file__).resolve().parents[2] / "demo-files" / "payment-logs.json").read_text())

    def upload(self, records):
        file = SimpleUploadedFile("logs.json", json.dumps(records).encode(), content_type="application/json")
        return self.client.post("/api/logs/upload/", {"file": file}, format="multipart")

    def test_demo_upload_and_repeat(self):
        response = self.upload(self.records)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["accepted"], 14)
        self.assertEqual(LogEntry.objects.count(), 14)
        self.assertEqual(PipelineRun.objects.count(), 1)
        self.assertEqual(PipelineRun.objects.get().status, "completed")
        response = self.upload(self.records)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["duplicate"], 14)
        self.assertEqual(LogEntry.objects.count(), 14)

    def test_duplicate_within_upload_and_invalid_record(self):
        response = self.upload([self.records[0], self.records[0], {"message": "invalid"}])
        self.assertEqual(response.status_code, 200)
        summary = response.json()["summary"]
        self.assertEqual((summary["accepted"], summary["duplicate"], summary["rejected"]), (1, 1, 1))

    def test_manual_ingestion_returns_json(self):
        response = self.client.post("/api/logs/ingest/", {"records": self.records[:1]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["accepted"], 1)
        self.assertEqual(PipelineRun.objects.count(), 1)
