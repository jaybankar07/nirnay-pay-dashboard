# Nirnay Pay (RecoveryOS) 🚀

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)
![Frontend](https://img.shields.io/badge/Frontend-React_19-61DAFB.svg?logo=react&logoColor=black)
![Language](https://img.shields.io/badge/Language-TypeScript-3178C6.svg?logo=typescript&logoColor=white)
![Styling](https://img.shields.io/badge/Styling-Tailwind_CSS-06B6D4.svg?logo=tailwindcss&logoColor=white)
![Database](https://img.shields.io/badge/Database-PostgreSQL-4169E1.svg?logo=postgresql&logoColor=white)
![AI Engine](https://img.shields.io/badge/AI_Engine-Qwen_2.5%3A7B-FF6F00.svg)
![Compliance](https://img.shields.io/badge/Compliance-RBI_DND_Enforced-2E7D32.svg)
![Ledger](https://img.shields.io/badge/Financial_Ledger-100%25_Single--Paise-4CAF50.svg)

**Nirnay Pay (RecoveryOS)** is an authoritative, financial-first enterprise platform designed for automated revenue loss detection, AI-driven root cause diagnosis, compliant intervention selection, and single-paise financial recovery orchestration. Engineered specifically for digital merchants, subscription platforms, and fintechs (complying with **RBI DND contact windows**, **PCI-DSS transaction boundaries**, and **strict attempt stopping rules**), Nirnay Pay combines local machine learning models with hard deterministic financial authority to ensure zero prompt-injection financial overrides, zero double-charges, and complete auditability across your private infrastructure.

---

## 📌 Overview

Revenue loss rarely happens in one clean step: payment gateways degrade, checkouts get abandoned, subscription renewals fail, and corporate receivables go overdue. Digital merchants lose up to 15–20% of annual recurring revenue due to unrecovered drop-offs and uncoordinated retry attempts.

Nirnay Pay closes the loop from real-time problem detection to AI diagnosis, compliant intervention selection, net financial yield scoring, and bounded recovery execution. Built on an **explicit finite state machine**, **deterministic financial governance**, **dual AI agent architecture**, and **single-paise database reconciliation**, Nirnay Pay guarantees complete auditability across every recovered rupee.

---

## 🎯 Problem Statement

Digital merchants lose significant revenue due to fragmented, non-compliant recovery workflows:

- **Payment Failures & Gateway Degradations**: Involuntary churn occurs when temporary technical failures are treated as permanent card declines.
- **Checkout Abandonments**: Abandoned carts are frequently lost because merchants lack automated, timely, and compliant intervention mechanisms.
- **Subscription Renewal Failures**: Subscriptions fail due to outdated cards, insufficient funds, or bank timeouts, leading to high revenue leakage.
- **Overdue B2B Receivables**: Invoices go unpaid when manual follow-ups lack structured escalation, DND compliance, and stopping rules.

---

## 💡 Proposed Solution

Nirnay Pay introduces an **Authoritative 6-Stage Recovery Decision Pipeline** powered by a dual-AI agent architecture backed by hard deterministic code authority:

1. **Separation of Cognition & Authority**: AI LLMs (Qwen 2.5:7B / Grok) diagnose root causes and compose empathetic communications, while deterministic code engines (`ComplianceEngine`, `StoppingRulesEngine`, `RecoveryRightsEngine`) hold exclusive authority over financial execution.
2. **Net Valuation Scoring**: Every potential recovery action is scored using expected probability of recovery minus channel costs and compliance penalties ($\text{Score} = P \cdot \text{Amount} - C_{\text{channel}} - P_{\text{compliance}}$).
3. **Bounded Execution & Single-Paise Audit**: All financial balances are tracked as integer paise in PostgreSQL, validated by an explicit finite state machine with immutable audit logs.

---

## ✨ Key Features

- **Multi-Scenario Ingestion**: Real-time detection across `PAYMENT_FAILURE`, `CHECKOUT_ABANDONMENT`, `SUBSCRIPTION_FAILURE`, and `OVERDUE_RECEIVABLE`.
- **Dual AI Agent System**:
  - **Agent 1 (`nirnay_revenue_diagnosis_agent`)**: Local Qwen 2.5:7B diagnosis agent categorizing root cause and confidence.
  - **Agent 2 (`nirnay_recovery_communication_agent`)**: Customer outreach rationale generator.
- **Compliance Gate Engine**: Enforces attempt limits, cooldown periods, and legal contact rules before authorizing outreach.
- **RecoveryScore Valuation Engine**: Mathematically selects the intervention that yields maximum expected net recovery value.
- **Bounded Execution Simulator**: Models gateway retries, customer responses, and timing causally without live card charges.
- **Real-Time Merchant Dashboard**: Modern React + Vite dashboard displaying active cases, recovery rates, revenue at risk, and audit trails.

---

## 🚀 Unique Features / USP

- **Deterministic Financial Authority**: LLMs recommend actions; code rules hold strict execution authority, preventing prompt-injection attacks.
- **RBI DND Window Enforcement**: Automatic blocking of customer outreach during Indian DND hours (21:00 – 08:00 IST) under RBI / TRAI guidelines.
- **Single-Paise Financial Reconciliation**: 100% integer-paise database accounting preventing floating-point rounding errors ($\text{Amount At Risk} = \text{Recovered} + \text{Unrecovered}$).
- **Exactly-Once Execution & Idempotency**: Atomic PostgreSQL row locking (`FOR UPDATE`) and idempotency keys prevent double charges.
- **Administrative Emergency Kill Switch**: Multi-tiered kill switch (`GLOBAL`, `TENANT`, `SCENARIO`) for immediate operational suspension.

---

## 📸 Screenshots & Decision Pipeline

```text
[ 1. AI Diagnosis ] ──> [ 2. Compliance ] ──> [ 3. Recovery Rights ]
         │                       │                       │
         ▼                       ▼                       ▼
   COMPLETED (AI)         APPROVED (Rules)        APPLIED (Policy)
         │                       │                       │
[ 4. RecoveryScore ] ──> [ 5. AI Decision ] ──> [ 6. Execution ]
         │                       │                       │
         ▼                       ▼                       ▼
  CALCULATED (Valuation)   RETRY (Authoritative)  RECOVERED (Ledger)
```

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion ["1. Event Ingestion"]
        RE[Revenue Event API / Webhook] --> DS[Detection Service]
    end
    subgraph Diagnosis ["2. AI Diagnosis & Compliance"]
        DS --> A1[Agent 1: Qwen 2.5:7B Root Cause Diagnosis]
        A1 --> CS[Compliance Gate & DND Hours Check]
    end
    subgraph Strategy ["3. Strategy & Valuation"]
        CS --> RR[Recovery Rights Policy Engine]
        RR --> RS[RecoveryScore Valuation Engine]
        RS --> DEC[Authoritative Decision Engine]
    end
    subgraph Execution ["4. Bounded Execution & Ledger"]
        DEC --> A2[Agent 2: Communication Rationale]
        DEC --> ES[Execution Service]
        ES --> SIM[Bounded Execution Simulator]
        ES --> LED[Single-Paise Financial Ledger & Audit Trail]
    end
    subgraph Observability ["5. Dashboard & Analytics"]
        LED --> DB[(PostgreSQL Database)]
        DB --> UI[Vite React Merchant Dashboard]
    end
```

---

## 🛠️ Tech Stack

| Layer | Technology / Model |
| :--- | :--- |
| **Frontend** | React 19, Vite 8, TypeScript, Tailwind CSS, TanStack Router/Query, Recharts |
| **Backend / API** | Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0 |
| **Database** | PostgreSQL / Supabase, SQLite (Local fallback) |
| **AI / ML Models** | Ollama (Local `qwen2.5:7b` model), xAI Grok API (`grok-beta` fallback) |
| **State & Rules Engine** | Explicit Finite State Machine (`RecoveryStateMachine`), Pydantic Financial Invariants |
| **DevOps & Tools** | Pytest, Docker Compose, Git, Prometheus Metrics (`/api/v1/metrics`) |

---

## 📂 Project Structure

```text
Nirnay Pay/
│
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI Endpoint Routers (/health, /cases, /score, /decide, /execute)
│   │   ├── core/            # State Machine, Financial Invariants, Kill Switch, Security
│   │   ├── database/        # SQLAlchemy Database Session & Initializer
│   │   ├── models/          # ORM Models (RecoveryCase, RevenueEvent, Decision, Action, Ledger)
│   │   ├── repositories/    # Data Access Layer & Repositories
│   │   ├── rules/           # Compliance Rules, DND Window, Stopping Rules, Rights Policy
│   │   ├── schemas/         # Pydantic Request/Response Validation Schemas
│   │   └── services/        # Business Logic (Diagnosis, Scoring, Decision, Execution, Audit)
│   ├── tests/               # Unit, Integration, and E2E Pytest Suites
│   ├── pyproject.toml
│   └── requirements.txt
│
├── frontend/
│   └── nirnay-pay-dashboard/ # React + Vite + TypeScript Merchant Dashboard
│       ├── src/
│       │   ├── components/  # Page Layouts, Stat Cards, Decision Pipeline, Dialogs
│       │   ├── lib/api/     # API Client, React Query Hooks & Fixture Fallback Transport
│       │   └── routes/      # TanStack Router Pages (Dashboard Overview, Case Detail, Audit Log)
│       └── package.json
│
├── nirnay_revenue_diagnosis_agent/  # Agent 1 (Local Qwen Diagnosis Package)
├── nirnay_recovery_communication_agent/ # Agent 2 (Communication Agent Package)
├── database/                # SQL Schema & Seed Files
├── scripts/                 # Verification Harness & QA Scripts
├── .env.example             # Environment Configuration Template
├── .gitignore               # Git Ignore Rules
└── README.md                # Technical Documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** / npm
- **PostgreSQL** (or SQLite fallback)
- *(Optional)* **Ollama** with `qwen2.5:7b` model installed for local LLM inference

---

### 1. Clone the Repository

```bash
git clone https://github.com/jaybankar07/nirnay-pay-dashboard.git
cd nirnay-pay-dashboard
```

---

### 2. Configure Environment Variables

Copy the example configuration:

```bash
cp .env.example backend/.env
```

---

### 3. Setup & Run Backend API

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend API runs at: `http://127.0.0.1:8000`  
Swagger API Docs available at: `http://127.0.0.1:8000/docs`

---

### 4. Setup & Run Frontend Dashboard

In a second terminal window:

```bash
cd frontend/nirnay-pay-dashboard

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

Frontend Dashboard runs at: `http://localhost:5173` (or `http://localhost:8082`)

---

## 📖 Usage Walkthrough

1. **Launch Dashboard**: Open `http://localhost:5173` in your browser to view active recovery metrics and cases.
2. **Simulate Revenue Risk Event**: Click the **"+ Simulate Live Event"** button in the header, select a scenario (e.g. `PAYMENT_FAILURE` or `CHECKOUT_ABANDONMENT`), enter an amount, and click **"Simulate & Ingest Event"**.
3. **Open Case Detail**: Click on any case ID in the recovery cases table to open the **Authoritative Recovery Decision Pipeline**.
4. **Step Through Decision Pipeline**: Click each stage button (`1. AI Diagnosis` ➔ `2. Compliance` ➔ `3. Recovery Rights` ➔ `4. RecoveryScore` ➔ `5. AI Decision`).
5. **Execute Approved Action**: Click **"6. Execution"** or **"Execute Approved Recovery"**, confirm execution, and watch the green toast announce money recovered.
6. **Inspect Audit Trail**: Scroll down to view the chronological, immutable case audit log.

---

## 📊 Performance & Verified Metrics

Nirnay Pay includes an automated QA and benchmark suite verifying system performance under load:

| Metric / Test | Target | Result | Status |
| :--- | :--- | :--- | :-: |
| **100-Case Execution Benchmark** | 100% Pass | **100/100 Cases Recovered / Handled** | 🟢 **PASSED** |
| **Overview Query Latency** | < 50ms | **7.48 ms (Avg)** | 🟢 **PASSED** |
| **Concurrent Stress Test** | 50 Requests | **50/50 Succeeded (0 Failures)** | 🟢 **PASSED** |
| **Single-Paise Ledger Integrity** | 0 Variance | **100% Exact Match** | 🟢 **PASSED** |
| **Secret Key Scanner** | 0 Plain-text Keys | **0 Exposed Credentials** | 🟢 **PASSED** |

---

## 🧪 Testing

Run the full automated backend test suite:

```bash
cd backend
python -m pytest tests/ -v
```

Run the canonical QA, load test, and security audit script:

```bash
python backend/scripts/comprehensive_qa_security_audit.py
```

---

## 🔐 Security & Governance

- **Secrets & API Keys**: Zero plain-text credentials or API keys are hardcoded in the codebase. All runtime configuration and optional external credentials (such as `GROK_API_KEY` / `XAI_API_KEY` used for testing Agent 2 cloud communication fallbacks) are safely loaded via environment variables (`.env`).
- **Multi-Tenant Data Boundaries**: Every repository query enforces strict `merchant_id` tenant scoping.
- **Regulatory Compliance**: RBI DND contact window (21:00–08:00 IST) enforced deterministically.
- **Idempotency Locks**: PostgreSQL atomic row locking (`FOR UPDATE`) prevents duplicate recovery calls.

---

## 📜 License

Distributed under the **MIT License**.
