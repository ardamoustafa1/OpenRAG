# Incident Response Plan

## Scope
This document outlines the standard operating procedure for handling security breaches, data leaks, or severe service degradation.

## Phases

### 1. Detection & Identification
- Monitor Prometheus Alerts (`alerts.yml`) for anomalies.
- Review Langfuse traces for unusual LLM generation patterns.

### 2. Containment
- **Immediate:** Disconnect affected Pods from the network (isolate). 
- **Short-term:** Rotate all compromised credentials using External Secrets Operator. Suspend the affected Tenant (`POST /tenants/{id}/suspend`).

### 3. Investigation
- Export Immutable Audit Logs (append-only Postgres partition).
- Collect Kubernetes Pod logs and Traefik access logs.
- Identify the root cause (e.g., CVE in a dependency, compromised JWT).

### 4. Eradication & Recovery
- Patch the vulnerability via GitHub Actions CI/CD.
- Trigger Velero restore if data was corrupted.
- Bring services back online progressively.

### 5. Regulatory Notification (KVKK/GDPR)
- **Deadline:** Within 72 hours of awareness.
- Notify the Data Protection Authority (KVKK Kurumu).
- Prepare transparent communication templates for affected Tenants.

## Forensics Evidence Collection
Audit logs exported via `app/compliance/audit_exporter.py` are cryptographically signed to maintain chain of custody.
