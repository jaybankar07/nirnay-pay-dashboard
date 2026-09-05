/**
 * DEVELOPMENT-ONLY transport adapter.
 *
 * Intercepts requests at the transport layer and replies with recorded fixture
 * payloads so the UI is reviewable before the backend exists. It contains no
 * business rules — it only looks up and returns stored data.
 */
import { auditFixture, caseFixtures, dashboardFixture, merchantFixture } from "./fixtures";
import type { RecoveryCaseDetail, Scenario, CustomerSegment } from "@/types/api";

type Query = Record<string, string | number | boolean | null | undefined> | undefined;

const store = new Map<string, RecoveryCaseDetail>(caseFixtures.map((c) => [c.case_id, { ...c }]));

function delay<T>(value: T, ms = 320): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

function str(query: Query, key: string): string | null {
  const value = query?.[key];
  if (value === null || value === undefined || value === "") return null;
  return String(value);
}

function num(query: Query, key: string, fallback: number): number {
  const value = str(query, key);
  const parsed = value === null ? Number.NaN : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function listCases(query: Query) {
  const scenario = str(query, "scenario");
  const status = str(query, "status");
  const segment = str(query, "customer_segment");
  const search = str(query, "search")?.toLowerCase() ?? null;
  const fromDate = str(query, "from_date");
  const toDate = str(query, "to_date");
  const page = Math.max(1, num(query, "page", 1));
  const pageSize = Math.max(1, num(query, "page_size", 10));

  const filtered = [...store.values()]
    .filter((c) => (scenario ? c.scenario === scenario : true))
    .filter((c) => (status ? c.status === status : true))
    .filter((c) => (segment ? c.customer_segment === segment : true))
    .filter((c) =>
      search
        ? c.case_id.toLowerCase().includes(search) || c.customer_name.toLowerCase().includes(search)
        : true,
    )
    .filter((c) => (fromDate ? c.created_at >= fromDate : true))
    .filter((c) => (toDate ? c.created_at <= `${toDate}T23:59:59Z` : true))
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  const start = (page - 1) * pageSize;
  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    page_size: pageSize,
  };
}

function executeCase(id: string) {
  const existing = store.get(id);
  if (!existing) throw new Error("Case not found");
  const action = existing.decision?.selected_action ?? existing.recommended_action ?? "REMINDER";
  const blocked = existing.compliance?.status === "BLOCKED";
  const updated: RecoveryCaseDetail = {
    ...existing,
    status: blocked ? "BLOCKED" : "RECOVERED",
    is_executable: false,
    executable_action: null,
    action_result: {
      action,
      status: blocked ? "BLOCKED" : "SUCCESS",
      recovered_amount: blocked ? null : existing.amount_at_risk,
      outcome_reason: blocked
        ? "No automatic recovery action executed."
        : "Recovery action completed and payment settled.",
      executed_at: new Date().toISOString(),
    },
    updated_at: new Date().toISOString(),
  };
  store.set(id, updated);
  return { case_id: id, action_result: updated.action_result, status: updated.status };
}

function createDetectedCase(body: any) {
  const newId = `RC-2026-${Math.floor(1060 + Math.random() * 900)}`;
  const scenario: Scenario = body?.event_type || "PAYMENT_FAILURE";
  const customerSegment: CustomerSegment = body?.customer_segment || "LOYAL";
  const customerName = body?.customer_name || "Rajesh Kumar";
  const amountPaise = body?.amount_paise || 249900;

  const newCase: RecoveryCaseDetail = {
    case_id: newId,
    merchant_id: body?.merchant_id || "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    customer_id: body?.customer_id || `cust_${Date.now()}`,
    customer_name: customerName,
    customer_segment: customerSegment,
    scenario: scenario,
    amount_at_risk: amountPaise,
    status: "DIAGNOSED",
    recovery_score: 84,
    recommended_action: "RETRY",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    diagnosis: {
      root_cause: "Temporary Payment Degraded",
      confidence: 0.91,
      mode: "AI",
      rationale: `AI Diagnosis (Agent 1): Event detected for ${customerName} (${scenario}). Recommended automated retry.`,
    },
    compliance: {
      status: "APPROVED",
      allowed_actions: ["RETRY", "REMINDER"],
      blocked_actions: ["ESCALATE"],
      blocking_reason: null,
      attempt_count: 0,
    },
    recovery_rights: {
      segment: customerSegment,
      recommended_treatment: "GRACE_PERIOD",
      business_reason: "High customer lifetime value. Priority recovery rules applied.",
    },
    score: {
      expected_recovery_probability: 0.88,
      channel_cost: 0,
      compliance_penalty: 0,
      score: 84,
    },
    decision: {
      selected_action: "RETRY",
      mode: "RULE",
      rationale: "Selected retry due to high expected probability of yielding full recovery.",
    },
    is_executable: true,
    executable_action: "RETRY",
    action_result: null,
  };

  store.set(newId, newCase);
  return {
    event_id: `evt_${Date.now()}`,
    case_id: newId,
    status: "DETECTED",
  };
}

function createFallbackCaseDetail(id: string): RecoveryCaseDetail {
  return {
    case_id: id,
    merchant_id: "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    customer_id: "cust_fallback_001",
    customer_name: "Rajesh Kumar",
    customer_segment: "LOYAL",
    scenario: "PAYMENT_FAILURE",
    amount_at_risk: 249900,
    status: "APPROVED",
    recovery_score: 84,
    recommended_action: "RETRY",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    diagnosis: {
      root_cause: "Temporary Gateway Timeout",
      confidence: 0.88,
      mode: "AI",
      rationale: "AI Diagnosis: Event detected for Rajesh Kumar. Gateway timeout observed on payment attempt.",
    },
    compliance: {
      status: "APPROVED",
      allowed_actions: ["RETRY", "REMINDER"],
      blocked_actions: ["ESCALATE"],
      blocking_reason: null,
      attempt_count: 0,
    },
    recovery_rights: {
      segment: "LOYAL",
      recommended_treatment: "GRACE_PERIOD",
      business_reason: "High customer lifetime value. Priority recovery rules applied.",
    },
    score: {
      expected_recovery_probability: 0.85,
      channel_cost: 0,
      compliance_penalty: 0,
      score: 84,
    },
    decision: {
      selected_action: "RETRY",
      mode: "RULE",
      rationale: "Selected retry based on high expected probability of yielding full recovery.",
    },
    is_executable: true,
    executable_action: "RETRY",
    action_result: null,
  };
}

export function fixtureTransport<T>(method: "GET" | "POST", path: string, query: Query, body?: unknown): Promise<T> {
  const caseMatch = /^\/recovery-cases\/([^/]+)(\/[a-z-]+)?$/.exec(path);

  if (path === "/health") return delay({ status: "ok", version: "fixture" }, 120) as Promise<T>;
  if (path.startsWith("/merchants/")) return delay(merchantFixture) as Promise<T>;
  if (path === "/dashboard/summary") return delay(dashboardFixture()) as Promise<T>;
  if (path === "/dashboard/cases" || path === "/recovery-cases") {
    if (method === "GET") return delay(listCases(query)) as Promise<T>;
  }

  if (caseMatch) {
    const id = caseMatch[1]!;
    const sub = caseMatch[2];
    let detail = store.get(id);
    if (!detail) {
      detail = createFallbackCaseDetail(id);
      store.set(id, detail);
    }

    if (!sub) return delay({ ...detail }) as Promise<T>;
    if (sub === "/audit") return delay(auditFixture(detail)) as Promise<T>;
    if (sub === "/execute") return delay(executeCase(id), 900) as Promise<T>;
    if (sub === "/diagnose") return delay(detail.diagnosis) as Promise<T>;
    if (sub === "/compliance-check") return delay(detail.compliance) as Promise<T>;
    if (sub === "/recovery-rights") return delay(detail.recovery_rights) as Promise<T>;
    if (sub === "/score") return delay(detail.score) as Promise<T>;
    if (sub === "/decide") return delay(detail.decision) as Promise<T>;
  }

  if (path === "/detect") {
    return delay(createDetectedCase(body), 500) as Promise<T>;
  }

  if (path === "/batch-runs") {
    return delay({ status: "accepted", batch_run_id: `batch_${Date.now()}` }) as Promise<T>;
  }

  return Promise.reject(new Error(`No fixture for ${method} ${path}`));
}
