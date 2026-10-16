import json
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from ai.services import IncidentAnalysis
from incidents.models import Incident
from investigations.models import Investigation
from knowledge.models import KnowledgeDocument, DocumentChunk
from logs.services import ingest_records


class InvestigationFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", email="owner@example.test")
        self.other = get_user_model().objects.create_user(username="other", email="other@example.test")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        records = json.loads((Path(__file__).resolve().parents[2] / "demo-files/payment-logs.json").read_text())
        ingest_records(records, self.user)
        ingest_records(records, self.other)
        for user in (self.user, self.other):
            doc = KnowledgeDocument.objects.create(user=user, title=user.username, content="payment timeout", status="indexed")
            DocumentChunk.objects.create(document=doc, chunk_index=0, content="payment timeout check gateway", embedding=[0]*8)
        self.assertEqual(self.client.post("/api/incidents/detect/").status_code, 200)
        self.incident = Incident.objects.get(user=self.user)

    @patch("knowledge.services.embed_text", return_value=[0]*8)
    @patch("agents.runner.generate_incident_analysis")
    def test_full_flow(self, generate, embed):
        generate.return_value = IncidentAnalysis(executive_summary="Timeouts require gateway checks", recommended_diagnostic_steps=["Check gateway availability"])
        self.assertEqual(self.incident.error_count, 12)
        self.assertEqual(self.incident.severity, "high")
        self.client.post("/api/incidents/detect/")
        self.assertEqual(Incident.objects.filter(user=self.user).count(), 1)
        response = self.client.post(f"/api/incidents/{self.incident.id}/investigate/")
        self.assertEqual(response.status_code, 200)
        report = self.client.get(f"/api/investigations/{response.json()['investigation_id']}/").json()
        self.assertEqual(report["status"], "completed")
        self.assertEqual(len(report["evidence"]["related_logs"]), 12)
        self.assertEqual(report["evidence"]["runbooks"][0]["document"], "owner")
        self.assertEqual(len(report["evidence"]["runbooks"]), 1)
        self.assertEqual(generate.call_args.args[3], report["evidence"]["runbooks"])
        self.assertEqual(report["result"]["recommended_diagnostic_steps"], ["Check gateway availability"])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/investigations/{report['id']}/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/incidents/{self.incident.id}/investigate/").status_code, 404)

    @patch("knowledge.services.embed_text", return_value=[0]*8)
    @patch("agents.runner.generate_incident_analysis", side_effect=RuntimeError("private provider failure"))
    def test_failure_preserves_evidence(self, generate, embed):
        response = self.client.post(f"/api/incidents/{self.incident.id}/investigate/")
        report = Investigation.objects.get(id=response.json()["investigation_id"])
        self.assertEqual(report.status, "failed")
        self.assertEqual(report.result, {})
        self.assertEqual(len(report.evidence["related_logs"]), 12)
        self.assertNotIn("private provider failure", report.error_message)
