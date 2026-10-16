# Payment service timeout runbook

Synthetic documentation for a demo; no real production system is described.

## Symptoms
The payment-service emits TimeoutError with messages such as Payment request 123 timed out. HTTP 504 responses may occur. Repeated timeouts establish a symptom, not a confirmed root cause.

## Possible causes and diagnostic checks
- Gateway outage: inspect the payment gateway status and compare failure times.
- Network connectivity issue: check DNS resolution and outbound connectivity from the service environment.
- Connection pool exhaustion: compare active connections and pending requests with configured limits.
- Slow upstream responses: compare observed request latency with the configured timeout.

## Remediation and verification
Choose a remediation only after confirming the cause. Restore connectivity for a verified network fault, or investigate leaked connections for confirmed pool exhaustion. Do not blindly increase timeouts or retry payments: retries require idempotency protection to avoid duplicate charges. After a fix, verify successful payment requests and check that timeout frequency decreases.
