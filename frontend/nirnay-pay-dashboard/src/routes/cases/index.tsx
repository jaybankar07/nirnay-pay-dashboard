import React, { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout/AppLayout";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import { useRecoveryCasesQuery } from "@/lib/api/queries";
import {
  formatINR,
  formatDateTime,
  humanizeToken,
} from "@/lib/format";
import {
  Search,
  Filter,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import type { Scenario, CaseStatus } from "@/types/api";

export const Route = createFileRoute("/cases/")({
  component: RecoveryCasesPage,
});

function RecoveryCasesPage() {
  const [search, setSearch] = useState("");
  const [scenario, setScenario] = useState<string>("ALL");
  const [status, setStatus] = useState<string>("ALL");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const queryParams = {
    page,
    page_size: pageSize,
    search: search ? search : undefined,
    scenario: scenario !== "ALL" ? (scenario as Scenario) : undefined,
    status: status !== "ALL" ? (status as CaseStatus) : undefined,
  };

  const { data, isLoading, isError, refetch } = useRecoveryCasesQuery(queryParams);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <AppLayout>
      <PageHeader
        title="Recovery Cases"
        description="Inspect and manage all revenue recovery cases across failure scenarios, compliance status, and recovery scores."
      />

      <SectionCard
        title="All Recovery Cases"
        description="Filter by scenario, status, or search by customer name and case ID."
      >
        {/* Filters & Search Toolbar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-4 pb-4 border-b border-border/40">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search case ID or customer..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9 text-xs"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            {/* Scenario Filter (Strict 4 scenarios only) */}
            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-muted-foreground hidden md:inline" />
              <Select
                value={scenario}
                onValueChange={(val) => {
                  setScenario(val);
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-[180px] text-xs h-9">
                  <SelectValue placeholder="Filter Scenario" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL" className="text-xs">All Scenarios</SelectItem>
                  <SelectItem value="PAYMENT_FAILURE" className="text-xs">Payment Failure</SelectItem>
                  <SelectItem value="CHECKOUT_ABANDONMENT" className="text-xs">Checkout Abandonment</SelectItem>
                  <SelectItem value="SUBSCRIPTION_FAILURE" className="text-xs">Subscription Failure</SelectItem>
                  <SelectItem value="OVERDUE_RECEIVABLE" className="text-xs">Overdue Receivable</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Status Filter */}
            <Select
              value={status}
              onValueChange={(val) => {
                setStatus(val);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[150px] text-xs h-9">
                <SelectValue placeholder="Filter Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL" className="text-xs">All Statuses</SelectItem>
                <SelectItem value="DETECTED" className="text-xs">Detected</SelectItem>
                <SelectItem value="DIAGNOSED" className="text-xs">Diagnosed</SelectItem>
                <SelectItem value="IN_PROGRESS" className="text-xs">In Progress</SelectItem>
                <SelectItem value="RECOVERED" className="text-xs">Recovered</SelectItem>
                <SelectItem value="BLOCKED" className="text-xs">Blocked</SelectItem>
                <SelectItem value="STOPPED" className="text-xs">Stopped</SelectItem>
                <SelectItem value="FAILED" className="text-xs">Failed</SelectItem>
              </SelectContent>
            </Select>

            {(search || scenario !== "ALL" || status !== "ALL") && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs h-9"
                onClick={() => {
                  setSearch("");
                  setScenario("ALL");
                  setStatus("ALL");
                  setPage(1);
                }}
              >
                Reset
              </Button>
            )}
          </div>
        </div>

        {/* Table Content State */}
        {isError ? (
          <ErrorState
            title="Failed to load recovery cases"
            message="Could not retrieve recovery cases from the server."
            onRetry={refetch}
          />
        ) : isLoading ? (
          <LoadingState rows={8} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="No matching recovery cases"
            description="Try clearing your search query or scenario filter."
            actionLabel="Reset Filters"
            onAction={() => {
              setSearch("");
              setScenario("ALL");
              setStatus("ALL");
              setPage(1);
            }}
          />
        ) : (
          <div className="space-y-4">
            <div className="rounded-md border border-border/60 overflow-x-auto">
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow>
                    <TableHead className="text-xs font-semibold">Case ID</TableHead>
                    <TableHead className="text-xs font-semibold">Customer</TableHead>
                    <TableHead className="text-xs font-semibold">Scenario</TableHead>
                    <TableHead className="text-xs font-semibold text-right">Amount At Risk</TableHead>
                    <TableHead className="text-xs font-semibold text-center">Score</TableHead>
                    <TableHead className="text-xs font-semibold">Action Recommended</TableHead>
                    <TableHead className="text-xs font-semibold">Status</TableHead>
                    <TableHead className="text-xs font-semibold">Created</TableHead>
                    <TableHead className="text-xs font-semibold text-right">Inspect</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((c) => (
                    <TableRow key={c.case_id} className="hover:bg-muted/30 transition-colors">
                      <TableCell className="font-mono text-xs font-bold text-foreground">
                        {c.case_id}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="text-xs font-medium text-foreground">{c.customer_name}</span>
                          <span className="text-[10px] text-muted-foreground">{humanizeToken(c.customer_segment)}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs font-medium text-foreground/80">
                        {humanizeToken(c.scenario)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-bold tabular-nums text-foreground">
                        {formatINR(c.amount_at_risk)}
                      </TableCell>
                      <TableCell className="text-center font-mono text-xs font-medium">
                        {c.recovery_score !== null ? (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-muted text-foreground">
                            {c.recovery_score.toFixed(0)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-xs font-mono font-medium">
                        {c.recommended_action ? (
                          <span className="inline-flex items-center gap-1 text-foreground">
                            <ShieldCheck className="w-3.5 h-3.5 text-sky-500" />
                            {c.recommended_action}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={c.status} />
                      </TableCell>
                      <TableCell className="font-mono text-[11px] text-muted-foreground tabular-nums">
                        {formatDateTime(c.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button asChild size="xs" variant="outline" className="text-xs">
                          <Link to={`/cases/${c.case_id}`}>
                            Details <ArrowRight className="w-3 h-3 ml-1" />
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-muted-foreground font-mono">
                Showing {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, data.total)} of {data.total} cases
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="text-xs h-8"
                >
                  <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Previous
                </Button>
                <span className="text-xs font-mono px-2 text-foreground">
                  {page} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="text-xs h-8"
                >
                  Next <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </SectionCard>
    </AppLayout>
  );
}
