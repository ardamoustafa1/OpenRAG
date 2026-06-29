# 🗺️ Roadmap — Enterprise RAG AI Platform

> This document outlines the planned features and milestones for the platform. Items marked ✅ are complete, 🚧 are in progress, and 📋 are planned.

---

## ✅ v0.1.0 — Foundation (Current)

- [x] Multi-tenant FastAPI backend with RBAC
- [x] JWT + TOTP MFA authentication
- [x] SAML 2.0 / OIDC SSO integration
- [x] Dense vector retrieval via Qdrant
- [x] Document ingestion pipeline (Celery + Unstructured)
- [x] SSE streaming chat with citation
- [x] Next.js frontend (dark mode, glassmorphism, WAI-ARIA)
- [x] Full observability stack (OpenTelemetry + Prometheus + Grafana + Loki)
- [x] Helm charts for Kubernetes deployment
- [x] CI/CD with Trivy, Bandit, Mypy, ESLint
- [x] Python + TypeScript SDK scaffolding

---

## 🚧 v0.2.0 — Hybrid Retrieval & Accuracy (Q3 2026)

- [ ] **BM25 Sparse Retrieval** — Full Reciprocal Rank Fusion (RRF) merge with dense results
- [ ] **Query Rewriting** — Multi-query generation for broader recall
- [ ] **Cross-Encoder Reranking** — Replace heuristic reranker with dedicated reranking model
- [ ] **Citation Highlighting** — Exact sentence-level citation anchoring in UI
- [ ] **RAG Evaluation Dashboard** — RAGAS metrics (faithfulness, context recall) live in admin panel
- [ ] **Conversation Memory** — Long-term summarized memory per user+collection pair
- [ ] **Table/Chart Parsing** — Structured data extraction from PDFs and XLSX

---

## 📋 v0.3.0 — Enterprise Controls (Q4 2026)

- [ ] **Row-Level Security (RLS)** — PostgreSQL-native document-level access control per user
- [ ] **Prompt Guardrails** — Tenant-configurable injection blockers and topic restrictions
- [ ] **Data Retention Policies** — Automatic document expiry and purge schedules
- [ ] **Compliance Export** — SOC 2 / GDPR-compliant audit log export (CSV/JSON)
- [ ] **Webhook System** — Outbound webhooks for document ingestion events and chat completions
- [ ] **Billing Dashboard** — Stripe-powered usage billing with per-tenant quota enforcement
- [ ] **Slack / Teams Integration** — Direct Q&A from enterprise chat tools

---

## 📋 v0.4.0 — Advanced AI (Q1 2027)

- [ ] **Agentic Workflows** — ReAct-style multi-step task execution
- [ ] **Tool Use / Function Calling** — Connect internal APIs to the assistant
- [ ] **Knowledge Graph** — Structured entity relationships alongside vector search
- [ ] **Fine-tuning Pipeline** — Domain adaptation of embedding and generative models
- [ ] **Federated Search** — Query across multiple isolated tenant collections with aggregated results
- [ ] **Vision RAG** — Image and diagram understanding in uploaded documents

---

## 📋 v1.0.0 — GA Release (Q2 2027)

- [ ] **One-click installer** — Automated `install.sh` with Docker/K8s auto-detection
- [ ] **Web UI installer wizard** — Browser-based setup with model selection and tenant creation
- [ ] **Air-gap bundle** — Complete offline package with all models included
- [ ] **SOC 2 Type II compliance** — Security audit and certification
- [ ] **Paid support tiers** — Community, Professional, Enterprise

---

## 💬 How to Influence the Roadmap

- Open a [GitHub Discussion](https://github.com/your-org/enterprise-rag/discussions) with your use case
- Upvote [existing feature requests](https://github.com/your-org/enterprise-rag/issues?q=is%3Aissue+label%3Afeature-request)
- Comment on any roadmap item — your vote counts!

---

> **Note:** Timelines are aspirational. The core team prioritizes based on community feedback, security requirements, and enterprise partner needs.
