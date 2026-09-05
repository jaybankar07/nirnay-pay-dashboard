import React, { useState, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout/AppLayout";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import { useRecoveryCasesQuery, useCaseAuditQuery } from "@/lib/api/queries";
import { formatDateTime } from "@/lib/format";
import {
  Search,
  History,
  ShieldCheck,
  Bot,
  User,
  Server,
  ArrowRight,
  Code,
} from "lucide-react";
import type { AuditEvent } from "@/types/api";

export const Route = createFileRoute("/audit")({
  component: AuditPage,
});

function AuditPage() {
  const [selectedCaseId, setSelectedCaseId] = useState<string>("");
  const [filterQuery, setFilterQuery] = useState("");

  const { data: casesData, isLoading: casesLoading } = useRecoveryCasesQuery({ page_size: 20 });

  // Automatically select the first case ID when cases load
  useEffect(() => {
    if (casesData?.items && casesData.items.length > 0 && !selectedCaseId) {
      const firstCase = casesData.items[0];
      const firstId = firstCase.case_id || (firstCase as any).id || "";
      if (firstId) {
        setSelectedCaseId(firstId);
      }
    }
  }, [casesData, selectedCaseId]);

  const {
    data: auditEvents,
    isLoading: auditLoading,
    isError,
    refetch,
  } = useCaseAuditQuery(selectedCaseId);

  const getActorBadge = (actor: string) => {
    const act = (actor || "").toUpperCase();
    if (act.includes("AI") || act.includes("DIAGNOSIS") || act.includes("COMMUNICATION")) {
      return (
        <Badge variant="outline" className="bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200">
          <Bot className="w-3 h-3 mr-1 text-purple-600" /> AI Agent
        </Badge>
      );
    }
    if (act.includes("SYSTEM") || act.includes("RULE") || act.includes("DETECTOR") || act.includes("SERVICE")) {
      return (
        <Badge variant="outline" className="bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300 border-sky-200">
          <Server className="w-3 h-3 mr-1 text-sky-600" /> System Rule
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200">
        <User className="w-3 h-3 mr-1 text-emerald-600" /> Merchant / User
      </Badge>
    );
  };

  const filteredEvents = (auditEvents || []).filter((evt) => {
    if (!filterQuery) return true;
    const q = filterQuery.toLowerCase();
    return (
      (evt.event_type || "").toLowerCase().includes(q) ||
      (evt.description || "").toLowerCase().includes(q) ||
      (evt.actor || "").toLowerCase().includes(q)
    );
  });

  return (
    <AppLayout>
      <PageHeader
        title="Compliance & Audit Log"
        description="Immutable, tamper-evident audit history of all revenue events, AI diagnoses, compliance gates, and recovery executions."
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Case Selector */}
        <div className="lg:col-span-1 space-y-4">
          <SectionCard title="Select Case for Audit" description="Choose a case to inspect detailed log entries">
            {casesLoading ? (
              <LoadingState rows={5} />
            ) : casesData?.items && casesData.items.length > 0 ? (
              <div className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1">
                {casesData.items.map((c) => {
                  const id = c.case_id || (c as any).id;
                  const isSelected = selectedCaseId === id;
                  return (
                    <button
                      key={id}
                      onClick={() => setSelectedCaseId(id)}
                      className={`w-full text-left p-2.5 rounded-md border text-xs transition-colors flex items-center justify-between ${
                        isSelected
                          ? "bg-primary text-primary-foreground border-primary font-semibold shadow-xs"
                          : "bg-card hover:bg-accent border-border/60 text-foreground"
                      }`}
                    >
                      <div>
                        <div className="font-mono font-bold">{id}</div>
                        <div className="text-[10px] opacity-80">{c.customer_name || "Customer"}</div>
                      </div>
                      <Badge variant="outline" className="text-[10px]">
                        {c.status}
                      </Badge>
                    </button>
                  );
                })}
              </div>
            ) : (
              <EmptyState title="No cases" description="No recovery cases available to audit." />
            )}
          </SectionCard>
        </div>

        {/* Right 3 Columns: Audit Event Log Table & Details */}
        <div className="lg:col-span-3 space-y-4">
          <SectionCard
            title={`Audit Log — Case ${selectedCaseId || "Loading..."}`}
            description="Chronological event ledger verified for compliance and regulatory inspection."
            action={
              selectedCaseId ? (
                <Button asChild size="xs" variant="outline" className="text-xs">
                  <Link to={`/cases/${selectedCaseId}`}>
                    View Case Details <ArrowRight className="w-3 h-3 ml-1" />
                  </Link>
                </Button>
              ) : undefined
            }
          >
            {/* Filter Input */}
            <div className="relative mb-4">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Filter audit events by event type, description, or actor..."
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                className="pl-9 text-xs"
              />
            </div>

            {!selectedCaseId && casesLoading ? (
              <LoadingState rows={6} />
            ) : isError ? (
              <ErrorState
                title="Failed to load audit events"
                message={`Could not load audit log for case '${selectedCaseId}'.`}
                onRetry={refetch}
              />
            ) : auditLoading ? (
              <LoadingState rows={6} />
            ) : filteredEvents.length === 0 ? (
              <EmptyState title="No audit events found" description="No event records match your search filter." />
            ) : (
              <div className="rounded-md border border-border/60 overflow-x-auto">
                <Table>
                  <TableHeader className="bg-muted/40">
                    <TableRow>
                      <TableHead className="text-xs font-semibold">Event ID</TableHead>
                      <TableHead className="text-xs font-semibold">Event Type</TableHead>
                      <TableHead className="text-xs font-semibold">Actor</TableHead>
                      <TableHead className="text-xs font-semibold">Timestamp</TableHead>
                      <TableHead className="text-xs font-semibold">Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredEvents.map((evt, idx) => (
                      <TableRow key={evt.event_id || idx} className="hover:bg-muted/30 transition-colors">
                        <TableCell className="font-mono text-xs font-semibold text-foreground">
                          {evt.event_id || `evt_${idx}`}
                        </TableCell>
                        <TableCell className="text-xs font-medium text-foreground">
                          <span className="font-mono bg-muted/60 px-1.5 py-0.5 rounded text-[11px] border border-border/40">
                            {evt.event_type}
                          </span>
                        </TableCell>
                        <TableCell>{getActorBadge(evt.actor)}</TableCell>
                        <TableCell className="font-mono text-[11px] text-muted-foreground tabular-nums">
                          {formatDateTime(evt.timestamp)}
                        </TableCell>
                        <TableCell className="text-xs text-foreground/90 max-w-xs leading-normal">
                          {evt.description}
                          {evt.details && (
                            <details className="mt-1">
                              <summary className="text-[10px] text-primary cursor-pointer font-mono inline-flex items-center gap-1 hover:underline">
                                <Code className="w-3 h-3" /> Event Payload Data
                              </summary>
                              <pre className="mt-1 p-2 rounded bg-muted/40 text-[10px] font-mono border border-border/40 overflow-x-auto text-foreground">
                                {JSON.stringify(evt.details, null, 2)}
                              </pre>
                            </details>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </SectionCard>
        </div>
      </div>
    </AppLayout>
  );
}
