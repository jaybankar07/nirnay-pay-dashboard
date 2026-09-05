import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
  HealthResponse,
  Merchant,
  DashboardSummary,
  Paginated,
  RecoveryCaseSummary,
  RecoveryCaseDetail,
  AuditEvent,
  CaseListParams,
  ExecuteResponse,
  Diagnosis,
  ComplianceResult,
  RecoveryRights,
  RecoveryScore,
  Decision,
  RecoveryAction,
  Scenario,
} from "@/types/api";

// Query Keys
export const queryKeys = {
  health: () => ["health"] as const,
  merchant: (id: string) => ["merchant", id] as const,
  dashboardSummary: (merchantId: string) => ["dashboard", "summary", merchantId] as const,
  recoveryCases: (params: CaseListParams) => ["recovery-cases", params] as const,
  recoveryCaseDetail: (caseId: string, merchantId: string) => ["recovery-case", caseId, merchantId] as const,
  caseAudit: (caseId: string, merchantId: string) => ["case-audit", caseId, merchantId] as const,
  heldOutEvaluation: () => ["held-out-evaluation"] as const,
};

export function useHeldOutEvaluationQuery() {
  return useQuery({
    queryKey: queryKeys.heldOutEvaluation(),
    queryFn: () => api.post<any>("/evaluation/run?dataset=HELD_OUT&seed=42"),
    staleTime: 60 * 1000,
    retry: 1,
  });
}


// 1. Health Query
export function useHealthQuery() {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => api.get<HealthResponse>("/health"),
    refetchInterval: 30000,
    retry: 1,
  });
}

// 2. Merchant Query
export function useMerchantQuery(merchantId = api.merchantId) {
  return useQuery({
    queryKey: queryKeys.merchant(merchantId),
    queryFn: () => api.get<Merchant>(`/merchants/${merchantId}`),
    staleTime: 5 * 60 * 1000,
  });
}

// 3. Dashboard Summary Query
export function useDashboardSummaryQuery(merchantId = api.merchantId) {
  return useQuery({
    queryKey: queryKeys.dashboardSummary(merchantId),
    queryFn: async () => {
      const res = await api.get<any>("/dashboard/summary", { merchant_id: merchantId });
      // Normalize raw backend or fixture keys
      return {
        revenue_at_risk: res.revenue_at_risk ?? res.revenue_at_risk_paise ?? 0,
        revenue_recovered: res.revenue_recovered ?? res.revenue_recovered_paise ?? 0,
        recovery_rate: res.recovery_rate ?? 0,
        active_cases: res.active_cases ?? 0,
        compliance_blocks: res.compliance_blocks ?? 0,
        performance: res.performance ?? [],
        scenario_breakdown: res.scenario_breakdown ?? [],
        comparison: res.comparison ?? {
          baseline: { recovery_rate: 0.0, revenue_recovered: 0, compliance_blocks: 0, stopped_cases: 0 },
          nirnay_pay: { recovery_rate: res.recovery_rate ?? 0, revenue_recovered: res.revenue_recovered ?? res.revenue_recovered_paise ?? 0, compliance_blocks: res.compliance_blocks ?? 0, stopped_cases: res.stopped_cases ?? 0 },
          data_source: res.data_source ?? "LIVE_DATABASE",
        },
      } as DashboardSummary;
    },
    refetchInterval: 60000,
  });
}

// 4. Recovery Cases Query (Paginated / Filtered)
export function useRecoveryCasesQuery(params: CaseListParams = {}) {
  const queryParams = {
    merchant_id: params.merchant_id ?? api.merchantId,
    scenario: params.scenario ?? undefined,
    status: params.status ?? undefined,
    customer_segment: params.customer_segment ?? undefined,
    search: params.search ?? undefined,
    from_date: params.from_date ?? undefined,
    to_date: params.to_date ?? undefined,
    page: params.page ?? 1,
    page_size: params.page_size ?? 10,
  };

  return useQuery({
    queryKey: queryKeys.recoveryCases(queryParams),
    queryFn: async () => {
      const res = await api.get<any>("/recovery-cases", queryParams);
      const rawItems = Array.isArray(res) ? res : res?.items || [];
      const total = res?.total ?? rawItems.length;
      const page = res?.page ?? queryParams.page;
      const pageSize = res?.page_size ?? queryParams.page_size;

      const items: RecoveryCaseSummary[] = rawItems.map((c: any) => ({
        case_id: c.case_id || c.id || "RC-2026-1001",
        customer_name: c.customer_name || c.customer_id || "Customer",
        customer_segment: c.customer_segment || "REGULAR",
        scenario: c.scenario || c.scenario_type || "PAYMENT_FAILURE",
        amount_at_risk: c.amount_at_risk ?? c.amount_at_risk_paise ?? 0,
        recovery_score: c.recovery_score ?? c.score ?? 75,
        recommended_action: c.recommended_action || c.action || "RETRY",
        status: c.status || "DETECTED",
        created_at: c.created_at || new Date().toISOString(),
      }));

      return {
        items,
        total,
        page,
        page_size: pageSize,
      };
    },
  });
}

// 5. Recovery Case Detail Query
export function useRecoveryCaseDetailQuery(caseId: string, merchantId = api.merchantId) {
  return useQuery({
    queryKey: queryKeys.recoveryCaseDetail(caseId, merchantId),
    queryFn: async () => {
      const res = await api.get<any>(`/recovery-cases/${caseId}`, { merchant_id: merchantId });
      return {
        case_id: res.case_id || res.id || caseId,
        merchant_id: res.merchant_id || merchantId,
        customer_id: res.customer_id || "cust_001",
        customer_name: res.customer_name || "Customer",
        customer_segment: res.customer_segment || "REGULAR",
        scenario: res.scenario || res.scenario_type || "PAYMENT_FAILURE",
        amount_at_risk: res.amount_at_risk ?? res.amount_at_risk_paise ?? 0,
        status: res.status || "DETECTED",
        recovery_score: res.recovery_score ?? 75,
        recommended_action: res.recommended_action || "RETRY",
        created_at: res.created_at || new Date().toISOString(),
        updated_at: res.updated_at || new Date().toISOString(),
        diagnosis: res.diagnosis || {
          root_cause: res.root_cause || "Temporary Failure",
          confidence: res.diagnosis_confidence || 0.85,
          mode: "AI",
          rationale: "Automated analysis indicates temporary gateway failure.",
        },
        compliance: res.compliance || {
          status: "APPROVED",
          allowed_actions: ["RETRY", "REMINDER"],
          blocked_actions: [],
          blocking_reason: null,
          attempt_count: 0,
        },
        recovery_rights: res.recovery_rights || {
          segment: res.customer_segment || "REGULAR",
          recommended_treatment: "STANDARD_RETRY",
          business_reason: "Standard recovery policy applies.",
        },
        score: res.score || {
          expected_recovery_probability: 0.8,
          channel_cost: 0,
          compliance_penalty: 0,
          score: 75,
        },
        decision: res.decision || {
          decision_id: res.decision_id || res.id || caseId,
          selected_action: "RETRY",
          mode: "RULE",
          rationale: "Selected retry based on positive score.",
        },
        is_executable: res.is_executable ?? (res.status !== "RECOVERED" && res.status !== "BLOCKED" && res.status !== "STOPPED"),
        executable_action: res.executable_action || "RETRY",
        action_result: res.action_result || null,
      } as RecoveryCaseDetail;
    },
    enabled: Boolean(caseId),
  });
}

// 6. Case Audit Query
export function useCaseAuditQuery(caseId: string, merchantId = api.merchantId) {
  return useQuery({
    queryKey: queryKeys.caseAudit(caseId, merchantId),
    queryFn: async () => {
      const res = await api.get<any>(`/recovery-cases/${caseId}/audit`, { merchant_id: merchantId });
      const rawList = Array.isArray(res) ? res : res?.items || [];
      return rawList.map((item: any, idx: number) => ({
        event_id: item.event_id || item.id || `evt_${caseId}_${idx}`,
        event_type: item.event_type || item.type || "EVENT",
        actor: item.actor_type || item.actor || "SYSTEM",
        timestamp: item.created_at || item.timestamp || new Date().toISOString(),
        description: item.description || item.event_data_json?.reason || item.event_data_json?.agent_name || `Audit event ${item.event_type} logged.`,
        details: item.event_data_json || item.details,
      })) as AuditEvent[];
    },
    enabled: Boolean(caseId),
  });
}

// 7. Execute Recovery Mutation
export function useExecuteRecoveryMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      caseId,
      decisionId,
      merchantId = api.merchantId,
    }: {
      caseId: string;
      decisionId: string;
      merchantId?: string;
    }) =>
      api.post<ExecuteResponse>(
        `/recovery-cases/${caseId}/execute`,
        { decision_id: decisionId },
        { merchant_id: merchantId }
      ),
    onSuccess: (data, variables) => {
      const merchantId = variables.merchantId ?? api.merchantId;
      queryClient.invalidateQueries({ queryKey: queryKeys.recoveryCaseDetail(variables.caseId, merchantId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.caseAudit(variables.caseId, merchantId) });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["recovery-cases"] });
    },
  });
}

// 8. Detect Event Mutation
export function useDetectEventMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: {
      merchant_id?: string;
      customer_id?: string;
      customer_name?: string;
      customer_segment?: string;
      event_type: Scenario;
      amount_paise: number;
      reason_code?: string;
    }) =>
      api.post<{ status: string; case_id?: string; event_id?: string }>("/detect", {
        merchant_id: payload.merchant_id ?? api.merchantId,
        customer_id: payload.customer_id,
        customer_name: payload.customer_name,
        customer_segment: payload.customer_segment,
        event_type: payload.event_type,
        amount_paise: payload.amount_paise,
        reason_code: payload.reason_code,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["recovery-cases"] });
    },
  });
}

// 9. Diagnose Case Mutation
export function useDiagnoseCaseMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ caseId, merchantId = api.merchantId, notes }: { caseId: string; merchantId?: string; notes?: string }) =>
      api.post<Diagnosis>(`/recovery-cases/${caseId}/diagnose`, { support_notes: notes }, { merchant_id: merchantId }),
    onSuccess: (_, variables) => {
      const merchantId = variables.merchantId ?? api.merchantId;
      queryClient.invalidateQueries({ queryKey: queryKeys.recoveryCaseDetail(variables.caseId, merchantId) });
    },
  });
}

// 10. Compliance Check Mutation
export function useComplianceCheckMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      caseId,
      candidateActions,
      merchantId = api.merchantId,
    }: {
      caseId: string;
      candidateActions: RecoveryAction[];
      merchantId?: string;
    }) =>
      api.post<ComplianceResult>(
        `/recovery-cases/${caseId}/compliance-check`,
        { candidate_actions: candidateActions },
        { merchant_id: merchantId }
      ),
    onSuccess: (_, variables) => {
      const merchantId = variables.merchantId ?? api.merchantId;
      queryClient.invalidateQueries({ queryKey: queryKeys.recoveryCaseDetail(variables.caseId, merchantId) });
    },
  });
}

// 11. Recovery Rights Mutation
export function useRecoveryRightsMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ caseId, merchantId = api.merchantId }: { caseId: string; merchantId?: string }) =>
      api.post<RecoveryRights>(`/recovery-cases/${caseId}/recovery-rights`, {}, { merchant_id: merchantId }),
    onSuccess: (_, variables) => {
      const merchantId = variables.merchantId ?? api.merchantId;
      queryClient.invalidateQueries({ queryKey: queryKeys.recoveryCaseDetail(variables.caseId, merchantId) });
    },
  });
}

// 12. Score Mutation
export function useCalculateScoreMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      caseId,
      candidateActions,
      merchantId = api.merchantId,
    }: {
      caseId: string;
      candidateActions: RecoveryAction[];
      merchantId?: string;
    }) =>
      api.post<RecoveryScore>(
        `/recovery-cases/${caseId}/score`,
        { candidate_actions: candidateActions },
        { merchant_id: merchantId }
      ),
    onSuccess: (_, variables) => {
      const merchantId = variables.merchantId ?? api.merchantId;
      queryClient.invalidateQueries({ queryKey: queryKeys.recoveryCaseDetail(variables.caseId, merchantId) });
    },
  });
}

// 13. Decision Mutation
export function useMakeDecisionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      caseId,
      candidateActions,
      merchantId = api.merchantId,
    }: {
      caseId: string;
      candidateActions: RecoveryAction[];
      merchantId?: string;
    }) =>
      api.post<Decision>(
        `/recovery-cases/${caseId}/decide`,
        { candidate_actions: candidateActions },
        { merchant_id: merchantId }
      ),
    onSuccess: (_, variables) => {
      const merchantId = variables.merchantId ?? api.merchantId;
      queryClient.invalidateQueries({ queryKey: queryKeys.recoveryCaseDetail(variables.caseId, merchantId) });
    },
  });
}

// 14. Batch Run Mutation
export function useBatchRunMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { merchant_id?: string; strategy: string; case_ids: string[] }) =>
      api.post<{ status: string; batch_run_id?: string }>("/batch-runs", {
        merchant_id: payload.merchant_id ?? api.merchantId,
        strategy: payload.strategy,
        case_ids: payload.case_ids,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["recovery-cases"] });
    },
  });
}
