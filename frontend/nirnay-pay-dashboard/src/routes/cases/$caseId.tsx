import React, { useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout/AppLayout";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { ConfirmationDialog } from "@/components/common/ConfirmationDialog";
import { Timeline } from "@/components/common/Timeline";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useRecoveryCaseDetailQuery,
  useCaseAuditQuery,
  useDiagnoseCaseMutation,
  useComplianceCheckMutation,
  useRecoveryRightsMutation,
  useCalculateScoreMutation,
  useMakeDecisionMutation,
  useExecuteRecoveryMutation,
} from "@/lib/api/queries";
import {
  formatINR,
  formatPercent,
  formatDateTime,
  humanizeToken,
} from "@/lib/format";
import { toast } from "sonner";
import {
  ArrowLeft,
  Zap,
  ShieldCheck,
  ShieldAlert,
  Bot,
  BrainCircuit,
  Scale,
  Calculator,
  CheckCircle2,
  User,
  Building2,
  Play,
  RotateCcw,
} from "lucide-react";

export const Route = createFileRoute("/cases/$caseId")({
  component: CaseDetailPage,
});

function CaseDetailPage() {
  const { caseId } = Route.useParams();
  const navigate = useNavigate();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const {
    data: caseDetail,
    isLoading: caseLoading,
    isError: caseError,
    refetch: refetchCase,
  } = useRecoveryCaseDetailQuery(caseId);

  const {
    data: auditEvents,
    isLoading: auditLoading,
    refetch: refetchAudit,
  } = useCaseAuditQuery(caseId);

  // Live Backend Mutations
  const diagnoseMutation = useDiagnoseCaseMutation();
  const complianceMutation = useComplianceCheckMutation();
  const rightsMutation = useRecoveryRightsMutation();
  const scoreMutation = useCalculateScoreMutation();
  const decisionMutation = useMakeDecisionMutation();
  const executeMutation = useExecuteRecoveryMutation();

  const refetchAll = () => {
    refetchCase();
    refetchAudit();
  };

  const handleRunDiagnosis = () => {
    diagnoseMutation.mutate(
      { caseId: caseDetail!.case_id },
      {
        onSuccess: () => {
          toast.success("Agent 1 (Revenue Diagnosis) executed successfully!");
          refetchAll();
        },
        onError: (err) => toast.error(err.message || "Diagnosis failed."),
      }
    );
  };

  const handleRunCompliance = () => {
    complianceMutation.mutate(
      { caseId: caseDetail!.case_id, candidateActions: ["RETRY", "REMINDER", "ESCALATE"] },
      {
        onSuccess: () => {
          toast.success("Compliance Gate evaluation completed!");
          refetchAll();
        },
        onError: (err) => toast.error(err.message || "Compliance check failed."),
      }
    );
  };

  const handleRunRights = () => {
    rightsMutation.mutate(
      { caseId: caseDetail!.case_id },
      {
        onSuccess: () => {
          toast.success("Recovery Rights LTV policy applied!");
          refetchAll();
        },
        onError: (err) => toast.error(err.message || "Recovery Rights check failed."),
      }
    );
  };

  const handleRunScore = () => {
    scoreMutation.mutate(
      { caseId: caseDetail!.case_id, candidateActions: ["RETRY", "REMINDER"] },
      {
        onSuccess: () => {
          toast.success("RecoveryScore formula valuation calculated!");
          refetchAll();
        },
        onError: (err) => toast.error(err.message || "Scoring calculation failed."),
      }
    );
  };

  const handleRunDecision = () => {
    decisionMutation.mutate(
      { caseId: caseDetail!.case_id, candidateActions: ["RETRY", "REMINDER"] },
      {
        onSuccess: () => {
          toast.success("Authoritative Decision & Agent 2 Communication generated!");
          refetchAll();
        },
        onError: (err) => toast.error(err.message || "Decision creation failed."),
      }
    );
  };

  const handleExecute = () => {
    if (!caseDetail || !caseDetail.decision) return;

    executeMutation.mutate(
      {
        caseId: caseDetail.case_id,
        decisionId: (caseDetail.decision as any).decision_id || "dec_001",
      },
      {
        onSuccess: (data) => {
          setConfirmOpen(false);
          toast.success(
            data.action_result.status === "SUCCESS"
              ? `Action ${data.action_result.action} executed successfully! Money Recovered.`
              : `Execution completed with status: ${data.action_result.status}`
          );
          refetchAll();
        },
        onError: (err) => {
          toast.error(err.message || "Failed to execute recovery action.");
        },
      }
    );
  };

  if (caseError) {
    return (
      <AppLayout>
        <PageHeader
          title={`Case ${caseId}`}
          breadcrumbs={<Link to="/cases" className="text-xs text-muted-foreground hover:text-foreground">← Back to Cases</Link>}
        />
        <ErrorState
          title="Case detail unavailable"
          message={`Could not load case '${caseId}' from the server.`}
          onRetry={refetchCase}
        />
      </AppLayout>
    );
  }

  if (caseLoading || !caseDetail) {
    return (
      <AppLayout>
        <LoadingState rows={10} />
      </AppLayout>
    );
  }

  const isBlocked = caseDetail.compliance?.status === "BLOCKED" || caseDetail.status === "BLOCKED";
  const isStopped = caseDetail.status === "STOPPED";
  const isRecovered = caseDetail.status === "RECOVERED";
  const isExecutable = caseDetail.is_executable && !isBlocked && !isStopped && !isRecovered;
  const selectedAction = caseDetail.decision?.selected_action || caseDetail.recommended_action || "REMINDER";

  return (
    <AppLayout>
      <PageHeader
        title={`Recovery Case ${caseDetail.case_id}`}
        description={`Merchant: ${caseDetail.merchant_id} | Created: ${formatDateTime(caseDetail.created_at)}`}
        breadcrumbs={
          <Button asChild variant="ghost" size="xs" className="p-0 text-xs text-muted-foreground hover:text-foreground">
            <Link to="/cases">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Recovery Cases
            </Link>
          </Button>
        }
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge status={caseDetail.status} />
            {isExecutable && (
              <Button
                size="sm"
                className="font-semibold text-xs shadow-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={() => setConfirmOpen(true)}
              >
                <Zap className="w-3.5 h-3.5 mr-1.5" /> Execute Approved Recovery
              </Button>
            )}
          </div>
        }
      />

      {/* Confirmation Dialog for Recovery Execution */}
      <ConfirmationDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={`Execute Recovery Action (${selectedAction})?`}
        isLoading={executeMutation.isPending}
        onConfirm={handleExecute}
        confirmLabel="Confirm Execution"
        description={
          <div className="space-y-3 pt-2 text-foreground/90">
            <p>You are about to authorize execution through the backend recovery orchestrator.</p>
            <div className="p-3 rounded-md bg-muted/50 border border-border/60 text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Case ID:</span>
                <span className="font-mono font-semibold">{caseDetail.case_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Amount At Risk:</span>
                <span className="font-mono font-bold text-amber-600">{formatINR(caseDetail.amount_at_risk)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Selected Action:</span>
                <Badge variant="outline" className="font-mono text-xs">{selectedAction}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Compliance Status:</span>
                <span className="font-semibold text-emerald-600">{caseDetail.compliance?.status || "APPROVED"}</span>
              </div>
            </div>
            <p className="text-[11px] text-muted-foreground italic">
              Note: The backend orchestrator is authoritative. Execution outcome will be audited automatically.
            </p>
          </div>
        }
      />

      {/* Visual & Interactive Decision Pipeline */}
      <SectionCard
        title="Authoritative Recovery Decision Pipeline"
        description="Click any stage button below to execute that step live against the FastAPI backend."
      >
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 pt-2">
          <Button
            size="xs"
            variant="outline"
            disabled={diagnoseMutation.isPending || isRecovered}
            onClick={handleRunDiagnosis}
            className="flex flex-col items-center justify-center p-3 h-auto border-border/60 hover:bg-purple-50 dark:hover:bg-purple-950/40"
          >
            <BrainCircuit className="w-4 h-4 mb-1 text-purple-600" />
            <span className="text-[10px] font-semibold text-muted-foreground">1. AI Diagnosis</span>
            <span className="text-[11px] font-mono font-bold mt-0.5 text-purple-700 dark:text-purple-300">
              {diagnoseMutation.isPending ? "Running..." : caseDetail.diagnosis ? "COMPLETED" : "RUN DIAGNOSIS"}
            </span>
          </Button>

          <Button
            size="xs"
            variant="outline"
            disabled={complianceMutation.isPending || isRecovered}
            onClick={handleRunCompliance}
            className="flex flex-col items-center justify-center p-3 h-auto border-border/60 hover:bg-sky-50 dark:hover:bg-sky-950/40"
          >
            <ShieldCheck className="w-4 h-4 mb-1 text-sky-600" />
            <span className="text-[10px] font-semibold text-muted-foreground">2. Compliance</span>
            <span className="text-[11px] font-mono font-bold mt-0.5 text-sky-700 dark:text-sky-300">
              {complianceMutation.isPending ? "Running..." : caseDetail.compliance?.status || "RUN CHECK"}
            </span>
          </Button>

          <Button
            size="xs"
            variant="outline"
            disabled={rightsMutation.isPending || isRecovered}
            onClick={handleRunRights}
            className="flex flex-col items-center justify-center p-3 h-auto border-border/60 hover:bg-indigo-50 dark:hover:bg-indigo-950/40"
          >
            <Scale className="w-4 h-4 mb-1 text-indigo-600" />
            <span className="text-[10px] font-semibold text-muted-foreground">3. Recovery Rights</span>
            <span className="text-[11px] font-mono font-bold mt-0.5 text-indigo-700 dark:text-indigo-300">
              {rightsMutation.isPending ? "Running..." : caseDetail.recovery_rights ? "APPLIED" : "APPLY RIGHTS"}
            </span>
          </Button>

          <Button
            size="xs"
            variant="outline"
            disabled={scoreMutation.isPending || isRecovered}
            onClick={handleRunScore}
            className="flex flex-col items-center justify-center p-3 h-auto border-border/60 hover:bg-amber-50 dark:hover:bg-amber-950/40"
          >
            <Calculator className="w-4 h-4 mb-1 text-amber-600" />
            <span className="text-[10px] font-semibold text-muted-foreground">4. RecoveryScore</span>
            <span className="text-[11px] font-mono font-bold mt-0.5 text-amber-700 dark:text-amber-300">
              {scoreMutation.isPending ? "Running..." : caseDetail.score ? "CALCULATED" : "CALCULATE"}
            </span>
          </Button>

          <Button
            size="xs"
            variant="outline"
            disabled={decisionMutation.isPending || isRecovered}
            onClick={handleRunDecision}
            className="flex flex-col items-center justify-center p-3 h-auto border-border/60 hover:bg-emerald-50 dark:hover:bg-emerald-950/40"
          >
            <Bot className="w-4 h-4 mb-1 text-emerald-600" />
            <span className="text-[10px] font-semibold text-muted-foreground">5. AI Decision</span>
            <span className="text-[11px] font-mono font-bold mt-0.5 text-emerald-700 dark:text-emerald-300">
              {decisionMutation.isPending ? "Running..." : caseDetail.decision ? selectedAction : "MAKE DECISION"}
            </span>
          </Button>

          <Button
            size="xs"
            variant="outline"
            disabled={executeMutation.isPending || !isExecutable}
            onClick={() => setConfirmOpen(true)}
            className="flex flex-col items-center justify-center p-3 h-auto border-emerald-500/50 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-200"
          >
            <Zap className="w-4 h-4 mb-1 text-emerald-600" />
            <span className="text-[10px] font-semibold text-muted-foreground">6. Execution</span>
            <span className="text-[11px] font-mono font-bold mt-0.5">
              {executeMutation.isPending ? "Executing..." : isRecovered ? "RECOVERED" : "EXECUTE"}
            </span>
          </Button>
        </div>
      </SectionCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Summary, AI Diagnosis, Governance & Decision */}
        <div className="lg:col-span-2 space-y-6">
          {/* Section 1: Case Summary & Customer Context */}
          <SectionCard title="Case Overview & Customer Context">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3 rounded-md bg-muted/40 border border-border/40 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                  <User className="w-4 h-4" /> Customer Details
                </div>
                <div className="text-sm font-bold text-foreground">{caseDetail.customer_name}</div>
                <div className="text-xs text-muted-foreground">Customer ID: <span className="font-mono text-foreground">{caseDetail.customer_id}</span></div>
                <div className="flex items-center gap-2 pt-1">
                  <span className="text-xs text-muted-foreground">Segment:</span>
                  <Badge variant="outline" className="text-xs">{humanizeToken(caseDetail.customer_segment)}</Badge>
                </div>
              </div>

              <div className="p-3 rounded-md bg-muted/40 border border-border/40 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                  <Building2 className="w-4 h-4" /> Revenue Scenario
                </div>
                <div className="text-sm font-bold text-foreground">{humanizeToken(caseDetail.scenario)}</div>
                <div className="text-xs text-muted-foreground">Amount At Risk:</div>
                <div className="text-xl font-mono font-extrabold text-amber-600">{formatINR(caseDetail.amount_at_risk)}</div>
              </div>
            </div>
          </SectionCard>

          {/* Section 2: AI-Assisted Diagnosis (Agent 1) */}
          <SectionCard
            title="AI-Assisted Revenue Diagnosis"
            description="Root cause analysis generated by Agent 1 (Revenue Diagnosis Agent)"
            action={
              <Badge variant="secondary" className="text-[11px]">
                Mode: {caseDetail.diagnosis?.mode || "AI"}
              </Badge>
            }
          >
            {caseDetail.diagnosis ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3 rounded-md border border-border/60 bg-purple-50/30 dark:bg-purple-950/20">
                    <span className="text-xs font-medium text-muted-foreground">Root Cause Diagnosis:</span>
                    <h4 className="text-sm font-bold text-purple-900 dark:text-purple-300 mt-1 capitalize">
                      {humanizeToken(caseDetail.diagnosis.root_cause)}
                    </h4>
                  </div>

                  <div className="p-3 rounded-md border border-border/60 bg-muted/30">
                    <span className="text-xs font-medium text-muted-foreground">Confidence Score:</span>
                    <div className="text-lg font-mono font-bold text-foreground mt-0.5">
                      {formatPercent(caseDetail.diagnosis.confidence, 1)}
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-md border border-border/40 bg-muted/20 text-xs">
                  <span className="font-semibold text-foreground">Diagnostic Evidence & Rationale:</span>
                  <p className="mt-1 text-muted-foreground leading-relaxed">{caseDetail.diagnosis.rationale}</p>
                </div>
              </div>
            ) : (
              <EmptyState title="Diagnosis pending" description="Agent 1 root cause diagnosis has not been executed yet." />
            )}
          </SectionCard>

          {/* Section 3: Governance — Compliance & Recovery Rights */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <SectionCard title="Compliance Gate" description="Deterministic regulatory safety rules">
              {caseDetail.compliance ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Compliance Status:</span>
                    <StatusBadge status={caseDetail.compliance.status} />
                  </div>
                  {caseDetail.compliance.blocking_reason && (
                    <div className="p-2.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 text-xs border border-amber-200">
                      <strong>Blocking Reason:</strong> {caseDetail.compliance.blocking_reason}
                    </div>
                  )}
                  <div className="text-xs">
                    <span className="text-muted-foreground">Allowed Actions: </span>
                    <span className="font-mono font-semibold">{caseDetail.compliance.allowed_actions.join(", ") || "None"}</span>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">Compliance check pending.</p>
              )}
            </SectionCard>

            <SectionCard title="Recovery Rights Policy" description="Merchant treatment rules">
              {caseDetail.recovery_rights ? (
                <div className="space-y-3">
                  <div className="text-xs">
                    <span className="text-muted-foreground">Recommended Treatment: </span>
                    <span className="font-semibold text-foreground">{caseDetail.recovery_rights.recommended_treatment}</span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-normal">
                    {caseDetail.recovery_rights.business_reason}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">Recovery rights policy check pending.</p>
              )}
            </SectionCard>
          </div>

          {/* Section 4: RecoveryScore Formula Breakdown */}
          <SectionCard title="RecoveryScore Valuation Engine" description="P(recovery) * Amount - ChannelCost - CompliancePenalty">
            {caseDetail.score ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-2.5 rounded bg-muted/40 border border-border/40">
                  <div className="text-[10px] uppercase text-muted-foreground font-semibold">Expected Prob</div>
                  <div className="text-sm font-mono font-bold text-foreground mt-1">{formatPercent(caseDetail.score.expected_recovery_probability, 1)}</div>
                </div>
                <div className="p-2.5 rounded bg-muted/40 border border-border/40">
                  <div className="text-[10px] uppercase text-muted-foreground font-semibold">Channel Cost</div>
                  <div className="text-sm font-mono font-bold text-foreground mt-1">{formatINR(caseDetail.score.channel_cost)}</div>
                </div>
                <div className="p-2.5 rounded bg-muted/40 border border-border/40">
                  <div className="text-[10px] uppercase text-muted-foreground font-semibold">Compliance Penalty</div>
                  <div className="text-sm font-mono font-bold text-foreground mt-1">{formatINR(caseDetail.score.compliance_penalty)}</div>
                </div>
                <div className="p-2.5 rounded bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200">
                  <div className="text-[10px] uppercase text-emerald-700 dark:text-emerald-300 font-semibold">Final Score</div>
                  <div className="text-sm font-mono font-bold text-emerald-800 dark:text-emerald-200 mt-1">{caseDetail.score.score.toFixed(1)}</div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">RecoveryScore calculation pending.</p>
            )}
          </SectionCard>
        </div>

        {/* Right 1 Column: Decision, Execution Result & Audit Timeline */}
        <div className="space-y-6">
          {/* Authoritative Decision Card */}
          <SectionCard title="Authoritative Decision" description="Selected by backend recovery engine">
            {caseDetail.decision ? (
              <div className="space-y-3">
                <div className="p-3 rounded-md bg-primary/5 border border-primary/20 text-center">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Selected Action</span>
                  <div className="text-xl font-mono font-extrabold text-primary mt-1">{caseDetail.decision.selected_action}</div>
                </div>
                <div className="text-xs space-y-1">
                  <div className="text-muted-foreground">Decision Mode: <span className="font-semibold text-foreground">{caseDetail.decision.mode}</span></div>
                  <div className="text-muted-foreground leading-relaxed pt-1">{caseDetail.decision.rationale}</div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Decision pending.</p>
            )}
          </SectionCard>

          {/* Action Execution Result */}
          <SectionCard title="Action Execution Result" description="Status returned after execution">
            {caseDetail.action_result ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Execution Status:</span>
                  <StatusBadge status={caseDetail.action_result.status} />
                </div>
                <div className="text-xs">
                  <span className="text-muted-foreground">Recovered Amount: </span>
                  <span className="font-mono font-bold text-emerald-600">{formatINR(caseDetail.action_result.recovered_amount ?? 0)}</span>
                </div>
                <p className="text-xs text-muted-foreground leading-normal bg-muted/30 p-2 rounded">
                  {caseDetail.action_result.outcome_reason}
                </p>
              </div>
            ) : (
              <div className="p-3 rounded border border-dashed border-border text-center text-xs text-muted-foreground">
                No recovery action executed yet.
              </div>
            )}
          </SectionCard>

          {/* Audit Trail */}
          <SectionCard title="Case Audit Trail" description="Complete chronological event history">
            {auditLoading ? (
              <LoadingState rows={4} />
            ) : auditEvents && auditEvents.length > 0 ? (
              <Timeline events={auditEvents} />
            ) : (
              <EmptyState title="No audit events" description="Audit log is currently empty." />
            )}
          </SectionCard>
        </div>
      </div>
    </AppLayout>
  );
}
