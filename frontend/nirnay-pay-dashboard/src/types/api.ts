/**
 * Types for the Nirnay Pay backend API contract.
 * The backend is the source of truth; the frontend only mirrors these shapes.
 */

export const SCENARIOS = [
  "PAYMENT_FAILURE",
  "CHECKOUT_ABANDONMENT",
  "SUBSCRIPTION_FAILURE",
  "OVERDUE_RECEIVABLE",
] as const;
export type Scenario = (typeof SCENARIOS)[number];

export const CASE_STATUSES = [
  "DETECTED",
  "DIAGNOSED",
  "IN_PROGRESS",
  "RECOVERED",
  "BLOCKED",
  "STOPPED",
  "FAILED",
  "HUMAN_REVIEW",
] as const;
export type CaseStatus = (typeof CASE_STATUSES)[number];

export const CUSTOMER_SEGMENTS = ["LOYAL", "REGULAR", "NEW", "AT_RISK"] as const;
export type CustomerSegment = (typeof CUSTOMER_SEGMENTS)[number];

export const RECOVERY_ACTIONS = [
  "RETRY",
  "WAIT",
  "REMINDER",
  "ESCALATE",
  "HUMAN_REVIEW",
  "STOP",
] as const;
export type RecoveryAction = (typeof RECOVERY_ACTIONS)[number];

export type DecisionMode = "AI" | "RULE" | "FALLBACK";
export type ComplianceStatus = "APPROVED" | "BLOCKED";
export type ActionResultStatus = "SUCCESS" | "FAILED" | "BLOCKED" | "STOPPED";

export interface HealthResponse {
  status: string;
  version?: string;
  uptime_seconds?: number;
}

export interface Merchant {
  merchant_id: string;
  name: string;
  legal_name?: string;
  environment?: string;
  currency?: string;
  timezone?: string;
}

export interface RecoveryCaseSummary {
  case_id: string;
  merchant_id: string;
  customer_id: string;
  customer_name: string;
  customer_segment: CustomerSegment;
  scenario: Scenario;
  amount_at_risk: number;
  currency: string;
  recovery_score: number | null;
  recommended_action: RecoveryAction | null;
  status: CaseStatus;
  created_at: string;
  updated_at?: string;
}

export interface Diagnosis {
  root_cause: string;
  confidence: number;
  mode: DecisionMode;
  rationale: string;
  diagnosed_at?: string;
}

export interface RecoveryRights {
  customer_segment: CustomerSegment;
  recommended_treatment: string;
  business_reason: string;
  applied_at?: string;
}

export interface ComplianceResult {
  status: ComplianceStatus;
  allowed_actions: RecoveryAction[];
  blocked_actions: RecoveryAction[];
  blocking_reason: string | null;
  attempt_count?: number | null;
  max_attempts?: number | null;
  checked_at?: string;
}

export interface RecoveryScore {
  score: number;
  expected_recovery_probability: number;
  amount_at_risk: number;
  channel_cost: number;
  compliance_penalty: number;
  calculated_at?: string;
}

export interface Decision {
  selected_action: RecoveryAction;
  mode: DecisionMode;
  rationale: string;
  confidence?: number | null;
  decided_at?: string;
}

export interface ActionResult {
  action: RecoveryAction;
  status: ActionResultStatus;
  recovered_amount: number | null;
  outcome_reason: string;
  executed_at?: string;
}

export interface RecoveryCaseDetail extends RecoveryCaseSummary {
  diagnosis: Diagnosis | null;
  recovery_rights: RecoveryRights | null;
  compliance: ComplianceResult | null;
  score: RecoveryScore | null;
  decision: Decision | null;
  action_result: ActionResult | null;
  is_executable: boolean;
  executable_action?: RecoveryAction | null;
}

export interface AuditEvent {
  event_id: string;
  case_id: string;
  event_type: string;
  actor: string;
  timestamp: string;
  description: string;
  details?: Record<string, unknown> | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScenarioBreakdown {
  scenario: Scenario;
  cases: number;
  amount_at_risk: number;
  amount_recovered: number;
  recovery_rate: number;
}

export interface PerformancePoint {
  period: string;
  revenue_at_risk: number;
  revenue_recovered: number;
}

export interface ComparisonMetrics {
  recovery_rate: number;
  revenue_recovered: number;
  revenue_at_risk: number;
  compliance_blocks: number;
  stopped_cases: number;
  total_cases: number;
}

export interface DashboardSummary {
  merchant_id: string;
  currency: string;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  active_cases: number;
  compliance_blocks: number;
  performance: PerformancePoint[];
  scenario_breakdown: ScenarioBreakdown[];
  comparison: {
    data_source: string;
    baseline: ComparisonMetrics;
    nirnay_pay: ComparisonMetrics;
  };
}

export interface CaseListParams {
  merchant_id?: string;
  scenario?: Scenario | null;
  status?: CaseStatus | null;
  customer_segment?: CustomerSegment | null;
  search?: string | null;
  from_date?: string | null;
  to_date?: string | null;
  page?: number;
  page_size?: number;
}

export interface ExecuteResponse {
  case_id: string;
  action_result: ActionResult;
  status: CaseStatus;
}
