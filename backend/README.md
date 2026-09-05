# Nirnay Pay (RecoveryOS) — Backend Service

Authoritative Python 3.11+ FastAPI backend for **Nirnay Pay (RecoveryOS)**, built for Track 03: AI Revenue Recovery (Razorpay AI Buildathon).

The backend acts as the authoritative **SOURCE OF TRUTH** for revenue risk management. The frontend is a client only and cannot bypass backend validation, compliance rules, stopping conditions, or Recovery Rights policies.

---

## Tech Stack
- **Framework**: Python 3.11+, FastAPI, Pydantic v2
- **Database & ORM**: PostgreSQL (Production) / SQLite (Development & Local), SQLAlchemy 2.x, Alembic
- **Testing**: Pytest, Pytest-Asyncio, HTTPX
- **Logging**: Structured JSON logging via `structlog`
- **Deployment**: Docker, Docker Compose

---

## Core Business Workflow Pipeline

Every recovery case follows this sequential pipeline:
```
Revenue Event (Payment Failure / Abandonment / Subscription / B2B Invoice)
    ↓
DetectionService (creates RecoveryCase, emits CASE_DETECTED audit event)
    ↓
DiagnosisService (determines root cause via rules or bounded LLM, supports AI fallback)
    ↓
ComplianceGate (deterministic check: APPROVED or BLOCKED)
    ↓
RecoveryRightsService (business policy mapping per customer segment & merchant policy)
    ↓
RecoveryScoreService (calculates score = P(recovery) * Amount - ChannelCost - CompliancePenalty)
    ↓
StoppingRules (re-verifies attempt limits, contact windows, diminishing returns)
    ↓
DecisionEngine (selects final executable action: RETRY, WAIT, REMINDER, ESCALATE, HUMAN_REVIEW, STOP)
    ↓
ExecutionService (runs transaction-safe bounded simulation producing SUCCESS, FAILED, or BLOCKED)
    ↓
AuditService (persists append-only immutable audit trail)
    ↓
MetricsService (updates merchant dashboard KPIs & synthetic baseline batch comparison)
```

---

## Local Development Setup

### 1. Installation
```bash
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
# source venv/bin/activate

pip install -e .[dev]
```

### 2. Seed Synthetic Data
```bash
python scripts/seed.py
```

### 3. Run Application Server
```bash
uvicorn app.main:app --reload --port 8000
```
Open interactive OpenAPI documentation at: `http://localhost:8000/docs`

---

## Running Automated Tests

```bash
pytest backend/tests -v
```

---

## Docker Deployment

To launch the production-ready PostgreSQL and FastAPI application stack:

```bash
docker compose up --build
```
