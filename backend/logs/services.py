import csv
import io
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from django.db import transaction
from django.utils import timezone as django_timezone

from .models import LogEntry, PipelineRun

ALLOWED_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def normalize_service_name(value: str | None) -> str:
    if value is None:
        return "unknown"
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "-", str(value).strip())
    return cleaned or "unknown"


def normalize_level(value: Any) -> str:
    level = str(value or "INFO").strip().upper()
    if level not in ALLOWED_LEVELS:
        return "INFO" if level in {"WARN", "WARNING"} else "INFO"
    return level


def parse_timestamp(value: Any) -> datetime:
    if value is None:
        raise ValueError("Timestamp is required")
    if isinstance(value, datetime):
        dt = value
    else:
        possible = str(value).strip()
        if possible.endswith("Z"):
            possible = possible[:-1] + "+00:00"
        dt = datetime.fromisoformat(possible)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_message(value: Any) -> str:
    return str(value or "").strip()[:2000]


def compute_fingerprint(record: dict[str, Any], user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "timestamp": parse_timestamp(record.get("timestamp")).isoformat(),
        "service": normalize_service_name(record.get("service_name")),
        "level": normalize_level(record.get("level")),
        "message": normalize_message(record.get("message")),
        "trace_id": str(record.get("trace_id") or "").strip(),
        "status_code": int(record.get("status_code") or 0) if str(record.get("status_code") or "").strip() else 0,
        "exception_type": str(record.get("exception_type") or "").strip(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def validate_record(record: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    normalized = {
        "timestamp": None,
        "service_name": None,
        "level": "INFO",
        "message": "",
        "environment": (record.get("environment") or "production").strip() or "production",
        "status_code": None,
        "trace_id": (record.get("trace_id") or "").strip(),
        "exception_type": (record.get("exception_type") or "").strip(),
        "stack_trace": (record.get("stack_trace") or "").strip(),
    }

    try:
        normalized["timestamp"] = parse_timestamp(record.get("timestamp"))
    except Exception:
        errors.append("Invalid timestamp")

    service = normalize_service_name(record.get("service_name"))
    normalized["service_name"] = service
    if not service or service == "unknown":
        errors.append("Missing service name")

    normalized["level"] = normalize_level(record.get("level"))
    normalized["message"] = normalize_message(record.get("message"))
    if not normalized["message"]:
        errors.append("Missing message")

    status_code_value = record.get("status_code")
    if status_code_value not in (None, ""):
        try:
            normalized["status_code"] = int(status_code_value)
        except (TypeError, ValueError):
            errors.append("Status code must be numeric")

    if record.get("environment") is not None:
        normalized["environment"] = str(record.get("environment")).strip() or "production"

    return normalized, errors


def get_rows_from_upload(file_obj) -> list[dict[str, Any]]:
    filename = (file_obj.name or "").lower()
    content = file_obj.read()
    if not content:
        return []
    if filename.endswith(".json"):
        data = json.loads(content.decode("utf-8"))
        if isinstance(data, dict):
            records = data.get("records") or data.get("logs") or [data]
        elif isinstance(data, list):
            records = data
        else:
            raise ValueError("Invalid JSON payload")
        return records
    if filename.endswith(".csv"):
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]
    raise ValueError("Unsupported file type")


def ingest_records(records: list[dict[str, Any]], user, source_name: str = "upload", pipeline=None) -> dict[str, Any]:
    accepted = rejected = duplicate = skipped = 0
    errors: list[str] = []
    detailed_errors: list[dict[str, Any]] = []
    valid_rows: list[LogEntry] = []
    seen_fingerprints = set()

    if not records:
        return {"accepted": 0, "rejected": 0, "duplicate": 0, "skipped": 0, "errors": [], "pipeline": None}

    for idx, row in enumerate(records):
        if row is None or not isinstance(row, dict):
            rejected += 1
            detailed_errors.append({"row": idx + 1, "error": "Malformed record"})
            continue

        normalized, validation_errors = validate_record(row)
        if validation_errors:
            rejected += 1
            detailed_errors.append({"row": idx + 1, "error": validation_errors})
            continue

        fingerprint = compute_fingerprint(normalized, user.id)
        if fingerprint in seen_fingerprints or LogEntry.objects.filter(user=user, fingerprint=fingerprint).exists():
            duplicate += 1
            continue

        entry = LogEntry(
            user=user,
            service_name=normalized["service_name"],
            level=normalized["level"],
            message=normalized["message"],
            environment=normalized["environment"],
            timestamp=parse_timestamp(normalized["timestamp"]),
            status_code=normalized.get("status_code"),
            trace_id=normalized.get("trace_id") or "",
            exception_type=normalized.get("exception_type") or "",
            stack_trace=normalized.get("stack_trace") or "",
            fingerprint=fingerprint,
            raw_payload=row,
        )
        valid_rows.append(entry)
        seen_fingerprints.add(fingerprint)
        accepted += 1

    with transaction.atomic():
        LogEntry.objects.bulk_create(valid_rows, batch_size=500)

    pipeline = pipeline or PipelineRun.objects.create(
        user=user,
        source_name=source_name,
        status="completed",
        total_records=len(records),
        accepted_records=accepted,
        rejected_records=rejected,
        duplicate_records=duplicate,
        skipped_records=skipped,
        processing_duration_ms=0,
        error_details=detailed_errors,
        metadata={"source": source_name},
    )

    return {
        "accepted": accepted,
        "rejected": rejected,
        "duplicate": duplicate,
        "skipped": skipped,
        "errors": detailed_errors,
        "pipeline": pipeline.id,
    }


def create_pipeline_run(user, source_name, total_records):
    return PipelineRun.objects.create(
        user=user,
        source_name=source_name,
        status="running",
        total_records=total_records,
        metadata={"source": source_name},
        started_at=django_timezone.now(),
    )
