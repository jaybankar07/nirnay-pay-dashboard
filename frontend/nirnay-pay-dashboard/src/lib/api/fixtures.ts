/**
 * DEVELOPMENT-ONLY transport fixtures.
 *
 * These are recorded response payloads shaped exactly like the backend API
 * contract, used only while the backend is not deployed. There is no business
 * logic here: no compliance rules, no Recovery Rights rules, no scoring, no
 * decisioning. Set VITE_USE_FIXTURES=false to talk to the real API instead.
 */
import { MERCHANT_ID } from "./config";
import type {
  ActionResult,
  AuditEvent,
  ComplianceResult,
  CustomerSegment,
  DashboardSummary,
  Decision,
  Diagnosis,
  Merchant,
  RecoveryAction,
  RecoveryCaseDetail,
  RecoveryRights,
  RecoveryScore,
  Scenario,
} from "@/types/api";

export const merchantFixture: Merchant = {
  merchant_id: MERCHANT_ID,
  name: "Aurelia Commerce",
  legal_name: "Aurelia Commerce Private Limited",
  environment: "sandbox",
  currency: "INR",
  timezone: "Asia/Kolkata",
};

type Seed = {
  customer: string;
  segment: CustomerSegment;
  scenario: Scenario;
  amount: number;
  score: number | null;
  action: RecoveryAction | null;
  status: RecoveryCaseDetail["status"];
  compliance: "APPROVED" | "BLOCKED";
  mode: "AI" | "RULE" | "FALLBACK";
  rootCause: string;
  rationale: string;
  treatment: string;
  businessReason: string;
  outcome: ActionResult["status"] | null;
  recovered: number | null;
  outcomeReason: string;
  executable: boolean;
};

const seeds: Seed[] = [
  {
    customer: "Ishaan Mehta",
    segment: "LOYAL",
    scenario: "PAYMENT_FAILURE",
    amount: 248000,
    score: 82,
    action: "WAIT",
    status: "IN_PROGRESS",
    compliance: "APPROVED",
    mode: "AI",
    rootCause: "Temporary Payment Failure",
    rationale: "Customer recently replaced their card.",
    treatment: "GRACE PERIOD",
    businessReason:
      "Protect long-term customer value instead of aggressively pursuing a single failed payment.",
    outcome: null,
    recovered: null,
    outcomeReason: "Awaiting grace period expiry before any recovery action.",
    executable: true,
  },
  {
    customer: "Rhea Kapoor",
    segment: "REGULAR",
    scenario: "CHECKOUT_ABANDONMENT",
    amount: 64500,
    score: 71,
    action: "REMINDER",
    status: "IN_PROGRESS",
    compliance: "APPROVED",
    mode: "AI",
    rootCause: "Checkout Drop-off At Payment Step",
    rationale: "Session ended on the UPI intent screen after a single attempt.",
    treatment: "SINGLE NUDGE",
    businessReason: "One low-friction reminder preserves intent without eroding trust.",
    outcome: null,
    recovered: null,
    outcomeReason: "Reminder queued for the approved channel.",
    executable: true,
  },
  {
    customer: "Kabir Nair",
    segment: "AT_RISK",
    scenario: "SUBSCRIPTION_FAILURE",
    amount: 189000,
    score: 46,
    action: "HUMAN_REVIEW",
    status: "HUMAN_REVIEW",
    compliance: "APPROVED",
    mode: "RULE",
    rootCause: "Mandate Revoked By Issuer",
    rationale: "Mandate is no longer active, so automated retries cannot succeed.",
    treatment: "MANUAL OUTREACH",
    businessReason: "High-value churn risk warrants a human owner rather than automation.",
    outcome: null,
    recovered: null,
    outcomeReason: "Assigned to the recovery operations queue.",
    executable: false,
  },
  {
    customer: "Ananya Iyer",
    segment: "LOYAL",
    scenario: "OVERDUE_RECEIVABLE",
    amount: 1250000,
    score: 88,
    action: "ESCALATE",
    status: "RECOVERED",
    compliance: "APPROVED",
    mode: "AI",
    rootCause: "Invoice Approval Delay",
    rationale: "Finance contact confirmed the invoice was pending internal approval.",
    treatment: "STRUCTURED FOLLOW-UP",
    businessReason: "Account has a clean 24-month payment history worth preserving.",
    outcome: "SUCCESS",
    recovered: 1250000,
    outcomeReason: "Full settlement received after escalation to the finance contact.",
    executable: false,
  },
  {
    customer: "Devansh Rao",
    segment: "NEW",
    scenario: "PAYMENT_FAILURE",
    amount: 32000,
    score: 39,
    action: "STOP",
    status: "BLOCKED",
    compliance: "BLOCKED",
    mode: "RULE",
    rootCause: "Repeated Insufficient Funds",
    rationale: "Attempt ceiling for this window has already been reached.",
    treatment: "NO CONTACT",
    businessReason: "Communication limits take precedence over recovery upside.",
    outcome: "BLOCKED",
    recovered: null,
    outcomeReason: "No automatic recovery action executed.",
    executable: false,
  },
  {
    customer: "Meera Joshi",
    segment: "REGULAR",
    scenario: "SUBSCRIPTION_FAILURE",
    amount: 74800,
    score: 76,
    action: "RETRY",
    status: "RECOVERED",
    compliance: "APPROVED",
    mode: "AI",
    rootCause: "Transient Bank Decline",
    rationale: "Issuer returned a soft decline that typically clears within a day.",
    treatment: "STANDARD RETRY",
    businessReason: "Low-cost retry with high historical success for this segment.",
    outcome: "SUCCESS",
    recovered: 74800,
    outcomeReason: "Retry authorised on the second attempt.",
    executable: false,
  },
  {
    customer: "Arjun Sethi",
    segment: "AT_RISK",
    scenario: "CHECKOUT_ABANDONMENT",
    amount: 15600,
    score: 28,
    action: "STOP",
    status: "STOPPED",
    compliance: "APPROVED",
    mode: "FALLBACK",
    rootCause: "Low Purchase Intent",
    rationale: "Model unavailable; fallback path selected the conservative action.",
    treatment: "NO FOLLOW-UP",
    businessReason: "Recovery cost outweighs the expected value of this cart.",
    outcome: "STOPPED",
    recovered: null,
    outcomeReason: "Case closed without contacting the customer.",
    executable: false,
  },
  {
    customer: "Saanvi Desai",
    segment: "LOYAL",
    scenario: "OVERDUE_RECEIVABLE",
    amount: 420000,
    score: 68,
    action: "REMINDER",
    status: "IN_PROGRESS",
    compliance: "APPROVED",
    mode: "RULE",
    rootCause: "Missed Payment Cycle",
    rationale: "First overdue cycle for an otherwise punctual account.",
    treatment: "GENTLE REMINDER",
    businessReason: "Preserve the relationship with a single courteous reminder.",
    outcome: null,
    recovered: null,
    outcomeReason: "Reminder scheduled within permitted contact hours.",
    executable: true,
  },
  {
    customer: "Vivaan Bhatt",
    segment: "REGULAR",
    scenario: "PAYMENT_FAILURE",
    amount: 96500,
    score: 61,
    action: "RETRY",
    status: "FAILED",
    compliance: "APPROVED",
    mode: "AI",
    rootCause: "Card Expired",
    rationale: "Card on file expired; retry attempted before requesting an update.",
    treatment: "STANDARD RETRY",
    businessReason: "Segment tolerates one automated retry before outreach.",
    outcome: "FAILED",
    recovered: null,
    outcomeReason: "Issuer declined the retry with the same reason code.",
    executable: false,
  },
  {
    customer: "Tara Menon",
    segment: "NEW",
    scenario: "CHECKOUT_ABANDONMENT",
    amount: 8900,
    score: 54,
    action: "REMINDER",
    status: "DIAGNOSED",
    compliance: "APPROVED",
    mode: "AI",
    rootCause: "Price Sensitivity At Checkout",
    rationale: "Cart reviewed three times before the session ended.",
    treatment: "SINGLE NUDGE",
    businessReason: "New customers respond well to one timely reminder.",
    outcome: null,
    recovered: null,
    outcomeReason: "Awaiting execution approval.",
    executable: true,
  },
  {
    customer: "Neel Chatterjee",
    segment: "LOYAL",
    scenario: "SUBSCRIPTION_FAILURE",
    amount: 156000,
    score: 79,
    action: "WAIT",
    status: "IN_PROGRESS",
    compliance: "APPROVED",
    mode: "AI",
    rootCause: "Bank Server Timeout",
    rationale: "Issuer downtime reported during the debit window.",
    treatment: "GRACE PERIOD",
    businessReason: "Loyal subscriber should not be penalised for issuer downtime.",
    outcome: null,
    recovered: null,
    outcomeReason: "Waiting for the next scheduled debit window.",
    executable: true,
  },
  {
    customer: "Aditi Verma",
    segment: "AT_RISK",
    scenario: "OVERDUE_RECEIVABLE",
    amount: 680000,
    score: 44,
    action: "ESCALATE",
    status: "DETECTED",
    compliance: "BLOCKED",
    mode: "RULE",
    rootCause: "Disputed Invoice Line Items",
    rationale: "An open dispute prevents automated collection activity.",
    treatment: "HOLD",
    businessReason: "Disputed balances must be resolved commercially before recovery.",
    outcome: "BLOCKED",
    recovered: null,
    outcomeReason: "No automatic recovery action executed.",
    executable: false,
  },
];

const ACTORS = [
  "detector.service",
  "diagnosis.agent",
  "compliance.engine",
  "recovery-rights.engine",
  "scoring.engine",
  "decision.engine",
  "execution.service",
  "outcome.tracker",
];

function isoAt(dayOffset: number, minuteOffset: number): string {
  const base = Date.UTC(2026, 7, 20, 4, 30, 0);
  return new Date(base - dayOffset * 86_400_000 + minuteOffset * 60_000).toISOString();
}

function caseId(index: number): string {
  return `RC-2026-${String(1041 + index).padStart(4, "0")}`;
}

function diagnosis(seed: Seed, index: number): Diagnosis {
  return {
    root_cause: seed.rootCause,
    confidence: 0.72 + ((index * 7) % 25) / 100,
    mode: seed.mode,
    rationale: seed.rationale,
    diagnosed_at: isoAt(index % 9, 12),
  };
}

function recoveryRights(seed: Seed, index: number): RecoveryRights {
  return {
    customer_segment: seed.segment,
    recommended_treatment: seed.treatment,
    business_reason: seed.businessReason,
    applied_at: isoAt(index % 9, 26),
  };
}

function compliance(seed: Seed, index: number): ComplianceResult {
  const blocked = seed.compliance === "BLOCKED";
  return {
    status: seed.compliance,
    allowed_actions: blocked ? ["WAIT", "HUMAN_REVIEW"] : ["RETRY", "REMINDER", "WAIT", "ESCALATE"],
    blocked_actions: blocked ? ["RETRY", "REMINDER", "ESCALATE"] : ["STOP"],
    blocking_reason: blocked
      ? "Contact attempt ceiling reached for the current consent window."
      : null,
    attempt_count: blocked ? 3 : 1,
    max_attempts: 3,
    checked_at: isoAt(index % 9, 18),
  };
}

function score(seed: Seed, index: number): RecoveryScore | null {
  if (seed.score === null) return null;
  return {
    score: seed.score,
    expected_recovery_probability: seed.score / 100,
    amount_at_risk: seed.amount,
    channel_cost: 12 + ((index * 5) % 40),
    compliance_penalty: seed.compliance === "BLOCKED" ? 25 : 0,
    calculated_at: isoAt(index % 9, 32),
  };
}

function decision(seed: Seed, index: number): Decision | null {
  if (!seed.action) return null;
  return {
    selected_action: seed.action,
    mode: seed.mode,
    rationale: seed.rationale,
    confidence: seed.mode === "FALLBACK" ? null : 0.68 + ((index * 4) % 28) / 100,
    decided_at: isoAt(index % 9, 40),
  };
}

function actionResult(seed: Seed, index: number): ActionResult | null {
  if (!seed.outcome || !seed.action) return null;
  return {
    action: seed.action,
    status: seed.outcome,
    recovered_amount: seed.recovered,
    outcome_reason: seed.outcomeReason,
    executed_at: isoAt(index % 9, 52),
  };
}

export const caseFixtures: RecoveryCaseDetail[] = seeds.map((seed, index) => ({
  case_id: caseId(index),
  merchant_id: MERCHANT_ID,
  customer_id: `cust_${String(2100 + index)}`,
  customer_name: seed.customer,
  customer_segment: seed.segment,
  scenario: seed.scenario,
  amount_at_risk: seed.amount,
  currency: "INR",
  recovery_score: seed.score,
  recommended_action: seed.action,
  status: seed.status,
  created_at: isoAt(index % 9, 0),
  updated_at: isoAt(index % 9, 55),
  diagnosis: diagnosis(seed, index),
  recovery_rights: recoveryRights(seed, index),
  compliance: compliance(seed, index),
  score: score(seed, index),
  decision: decision(seed, index),
  action_result: actionResult(seed, index),
  is_executable: seed.executable,
  executable_action: seed.executable ? seed.action : null,
}));

export function auditFixture(detail: RecoveryCaseDetail): AuditEvent[] {
  const steps: Array<{ type: string; description: string; ok: boolean }> = [
    { type: "DETECTED", description: `Revenue at risk detected for ${detail.customer_name}.`, ok: true },
    {
      type: "DIAGNOSED",
      description: detail.diagnosis ? `Root cause: ${detail.diagnosis.root_cause}.` : "Diagnosis pending.",
      ok: Boolean(detail.diagnosis),
    },
    {
      type: "COMPLIANCE_CHECKED",
      description: detail.compliance
        ? `Compliance ${detail.compliance.status.toLowerCase()}.`
        : "Compliance check pending.",
      ok: Boolean(detail.compliance),
    },
    {
      type: "RECOVERY_RIGHTS_APPLIED",
      description: detail.recovery_rights
        ? `Treatment ${detail.recovery_rights.recommended_treatment} for ${detail.recovery_rights.customer_segment} segment.`
        : "Recovery Rights pending.",
      ok: Boolean(detail.recovery_rights),
    },
    {
      type: "SCORE_CALCULATED",
      description: detail.score ? `RecoveryScore ${detail.score.score}.` : "Score pending.",
      ok: Boolean(detail.score),
    },
    {
      type: "DECISION_MADE",
      description: detail.decision
        ? `Action ${detail.decision.selected_action} selected via ${detail.decision.mode}.`
        : "Decision pending.",
      ok: Boolean(detail.decision),
    },
    {
      type: "ACTION_EXECUTED",
      description: detail.action_result
        ? `Action ${detail.action_result.action} executed.`
        : "No action executed yet.",
      ok: Boolean(detail.action_result),
    },
    {
      type: "OUTCOME",
      description: detail.action_result?.outcome_reason ?? "Outcome pending.",
      ok: Boolean(detail.action_result),
    },
  ];

  return steps
    .filter((step) => step.ok)
    .map((step, i) => ({
      event_id: `${detail.case_id}-evt-${i + 1}`,
      case_id: detail.case_id,
      event_type: step.type,
      actor: ACTORS[i] ?? "system",
      timestamp: isoAt(0, i * 6),
      description: step.description,
      details: { step: i + 1, case_status: detail.status },
    }));
}

export function dashboardFixture(): DashboardSummary {
  const atRisk = caseFixtures.reduce((sum, c) => sum + c.amount_at_risk, 0);
  const recovered = caseFixtures.reduce(
    (sum, c) => sum + (c.action_result?.status === "SUCCESS" ? (c.action_result.recovered_amount ?? 0) : 0),
    0,
  );
  const blocks = caseFixtures.filter((c) => c.compliance?.status === "BLOCKED").length;
  const stopped = caseFixtures.filter((c) => c.status === "STOPPED").length;
  const active = caseFixtures.filter((c) =>
    ["DETECTED", "DIAGNOSED", "IN_PROGRESS", "HUMAN_REVIEW"].includes(c.status),
  ).length;

  const scenarioBreakdown = (
    ["PAYMENT_FAILURE", "CHECKOUT_ABANDONMENT", "SUBSCRIPTION_FAILURE", "OVERDUE_RECEIVABLE"] as Scenario[]
  ).map((scenario) => {
    const rows = caseFixtures.filter((c) => c.scenario === scenario);
    const risk = rows.reduce((sum, c) => sum + c.amount_at_risk, 0);
    const rec = rows.reduce(
      (sum, c) => sum + (c.action_result?.status === "SUCCESS" ? (c.action_result.recovered_amount ?? 0) : 0),
      0,
    );
    return {
      scenario,
      cases: rows.length,
      amount_at_risk: risk,
      amount_recovered: rec,
      recovery_rate: risk > 0 ? rec / risk : 0,
    };
  });

  return {
    merchant_id: MERCHANT_ID,
    currency: "INR",
    revenue_at_risk: 2_500_000,
    revenue_recovered: 1_750_000,
    recovery_rate: 0.7,
    active_cases: active + 28,
    compliance_blocks: blocks + 2,
    performance: [
      { period: "Mar", revenue_at_risk: 1_820_000, revenue_recovered: 980_000 },
      { period: "Apr", revenue_at_risk: 2_040_000, revenue_recovered: 1_180_000 },
      { period: "May", revenue_at_risk: 2_260_000, revenue_recovered: 1_420_000 },
      { period: "Jun", revenue_at_risk: 2_180_000, revenue_recovered: 1_510_000 },
      { period: "Jul", revenue_at_risk: 2_420_000, revenue_recovered: 1_660_000 },
      { period: "Aug", revenue_at_risk: 2_500_000, revenue_recovered: 1_750_000 },
    ],
    scenario_breakdown: scenarioBreakdown,
    comparison: {
      data_source: "Synthetic / Simulated Data",
      baseline: {
        recovery_rate: 0.41,
        revenue_recovered: 1_025_000,
        revenue_at_risk: 2_500_000,
        compliance_blocks: 0,
        stopped_cases: 2,
        total_cases: 140,
      },
      nirnay_pay: {
        recovery_rate: 0.7,
        revenue_recovered: 1_750_000,
        revenue_at_risk: 2_500_000,
        compliance_blocks: 6,
        stopped_cases: 11,
        total_cases: 140,
      },
    },
  };
}
