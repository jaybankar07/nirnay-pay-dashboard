import React from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout/AppLayout";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import {
  useDashboardSummaryQuery,
  useRecoveryCasesQuery,
  useHeldOutEvaluationQuery,
} from "@/lib/api/queries";
import {
  formatINR,
  formatPercent,
  formatNumber,
  formatDateTime,
  humanizeToken,
} from "@/lib/format";
import {
  DollarSign,
  TrendingUp,
  ShieldAlert,
  AlertTriangle,
  ArrowRight,
  Activity,
  Layers,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from "recharts";

export const Route = createFileRoute("/")({
  component: DashboardOverview,
});

function DashboardOverview() {
  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = useDashboardSummaryQuery();

  const {
    data: recentCasesData,
    isLoading: casesLoading,
    isError: casesError,
    refetch: refetchCases,
  } = useRecoveryCasesQuery({ page: 1, page_size: 5 });

  const isLoading = summaryLoading || casesLoading;
  const isError = summaryError || casesError;

  return (
    <AppLayout>
      <PageHeader
        title="Revenue Recovery Overview"
        description="Real-time AI revenue risk diagnosis, compliance governance, and autonomous recovery execution."
        actions={
          <Button asChild size="sm" className="font-semibold text-xs shadow-xs">
            <Link to="/cases">
              View All Cases <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Link>
          </Button>
        }
      />

      {isError ? (
        <ErrorState
          title="Dashboard unavailable"
          message="Could not load recovery metrics from the backend service."
          onRetry={() => {
            refetchSummary();
            refetchCases();
          }}
        />
      ) : isLoading ? (
        <LoadingState rows={6} />
      ) : !summary ? (
        <EmptyState title="No summary data" description="No recovery summary records were returned by the backend." />
      ) : (
        <div className="space-y-6">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <StatCard
              title="Revenue At Risk"
              value={formatINR(summary.revenue_at_risk)}
              subtitle="Detected at-risk volume"
              icon={<DollarSign className="w-4 h-4 text-amber-600 dark:text-amber-400" />}
            />
            <StatCard
              title="Revenue Recovered"
              value={formatINR(summary.revenue_recovered)}
              subtitle="Settled & recovered"
              icon={<TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />}
              trend={{
                value: formatPercent(summary.recovery_rate),
                isPositive: summary.recovery_rate > 0.5,
              }}
            />
            <StatCard
              title="Recovery Rate"
              value={formatPercent(summary.recovery_rate, 1)}
              subtitle="Nirnay Pay recovery efficiency"
              icon={<Activity className="w-4 h-4 text-sky-600 dark:text-sky-400" />}
            />
            <StatCard
              title="Active Cases"
              value={formatNumber(summary.active_cases)}
              subtitle="In recovery pipeline"
              icon={<Layers className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />}
            />
            <StatCard
              title="Compliance Blocks"
              value={formatNumber(summary.compliance_blocks)}
              subtitle="Protected by governance"
              icon={<ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400" />}
            />
            <StatCard
              title="Stopped Cases"
              value={formatNumber(summary.comparison?.nirnay_pay?.stopped_cases ?? 0)}
              subtitle="Diminishing returns cap"
              icon={<AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400" />}
            />
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Performance Chart (Area) */}
            <SectionCard
              title="Recovery Performance Trend"
              description="Historical revenue at risk vs revenue successfully recovered"
              className="lg:col-span-2"
            >
              {summary.performance && summary.performance.length > 0 ? (
                <div className="h-72 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={summary.performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="gradRecovered" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradRisk" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-border/40" />
                      <XAxis dataKey="period" stroke="currentColor" className="text-[11px] text-muted-foreground" />
                      <YAxis stroke="currentColor" className="text-[11px] text-muted-foreground" tickFormatter={(v) => `₹${v / 1000}k`} />
                      <Tooltip
                        formatter={(val: number) => [formatINR(val), ""]}
                        contentStyle={{ backgroundColor: "var(--color-card)", borderColor: "var(--color-border)", borderRadius: "6px" }}
                      />
                      <Area type="monotone" dataKey="revenue_at_risk" name="Revenue At Risk" stroke="#f59e0b" fillOpacity={1} fill="url(#gradRisk)" strokeWidth={2} />
                      <Area type="monotone" dataKey="revenue_recovered" name="Revenue Recovered" stroke="#10b981" fillOpacity={1} fill="url(#gradRecovered)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No trend data" description="Performance timeline is currently empty." />
              )}
            </SectionCard>

            {/* Scenario Breakdown Chart */}
            <SectionCard
              title="Scenario Breakdown"
              description="Distribution of revenue risk across recovery scenarios"
            >
              {summary.scenario_breakdown && summary.scenario_breakdown.length > 0 ? (
                <div className="h-72 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={summary.scenario_breakdown} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-border/40" />
                      <XAxis dataKey="scenario" stroke="currentColor" className="text-[10px] text-muted-foreground" tickFormatter={(v) => v.split("_")[0]} />
                      <YAxis stroke="currentColor" className="text-[11px] text-muted-foreground" tickFormatter={(v) => `₹${v / 1000}k`} />
                      <Tooltip
                        formatter={(val: number) => [formatINR(val), "Amount At Risk"]}
                        labelFormatter={(lbl) => humanizeToken(String(lbl))}
                        contentStyle={{ backgroundColor: "var(--color-card)", borderColor: "var(--color-border)", borderRadius: "6px" }}
                      />
                      <Bar dataKey="amount_at_risk" name="Amount At Risk" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No scenario data" description="Scenario breakdown is currently empty." />
              )}
            </SectionCard>
          </div>

          {/* Held-Out Evaluation & Revenue Impact Section */}
          <SectionCard
            title="Held-Out Synthetic Evaluation & AI Revenue Impact"
            description="Same-world benchmark comparing Conventional Baseline vs. Nirnay RecoveryOS (Real Decision & Governance Pipeline)"
            action={
              <span className="inline-flex items-center rounded-md bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-500 ring-1 ring-amber-500/20 ring-inset">
                SYNTHETIC HELD-OUT EVALUATION — NOT PRODUCTION RESULTS
              </span>
            }
          >
            <HeldOutEvaluationSection />
          </SectionCard>

          {/* Recent Recovery Cases */}
          <SectionCard
            title="Recent Recovery Cases"
            description="Latest revenue events requiring diagnosis, compliance check, or execution"
            action={
              <Button asChild variant="outline" size="sm" className="text-xs">
                <Link to="/cases">View All Cases</Link>
              </Button>
            }
          >
            {recentCasesData?.items && recentCasesData.items.length > 0 ? (
              <div className="rounded-md border border-border/60 overflow-x-auto">
                <Table>
                  <TableHeader className="bg-muted/40">
                    <TableRow>
                      <TableHead className="text-xs font-semibold">Case ID</TableHead>
                      <TableHead className="text-xs font-semibold">Customer</TableHead>
                      <TableHead className="text-xs font-semibold">Scenario</TableHead>
                      <TableHead className="text-xs font-semibold text-right">Amount At Risk</TableHead>
                      <TableHead className="text-xs font-semibold">Status</TableHead>
                      <TableHead className="text-xs font-semibold">Created</TableHead>
                      <TableHead className="text-xs font-semibold text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentCasesData.items.map((c) => (
                      <TableRow key={c.case_id} className="hover:bg-muted/30 transition-colors">
                        <TableCell className="font-mono text-xs font-semibold text-foreground">
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
                        <TableCell>
                          <StatusBadge status={c.status} />
                        </TableCell>
                        <TableCell className="font-mono text-[11px] text-muted-foreground tabular-nums">
                          {formatDateTime(c.created_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button asChild size="xs" variant="ghost" className="text-xs hover:bg-accent">
                            <Link to={`/cases/${c.case_id}`}>
                              Inspect <ArrowRight className="w-3 h-3 ml-1" />
                            </Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <EmptyState title="No recent cases" description="No active recovery cases exist." />
            )}
          </SectionCard>
        </div>
      )}
    </AppLayout>
  );
}

function HeldOutEvaluationSection() {
  const { data: evalData, isLoading, isError } = useHeldOutEvaluationQuery();

  if (isLoading) return <LoadingState title="Running Held-Out Evaluation..." description="Executing same-world pipeline comparison against 30 held-out cases." />;
  if (isError || !evalData) return <EmptyState title="Evaluation Service Offline" description="Failed to run held-out evaluation." />;

  const baseline = evalData.baseline;
  const nirnay = evalData.nirnay;
  const incPaise = evalData.incremental_recovered_paise;
  const incRupees = incPaise / 100;
  const isPositive = incRupees >= 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="p-4 rounded-lg border border-border bg-card">
          <div className="text-xs font-medium text-muted-foreground">Baseline Recovery</div>
          <div className="text-xl font-bold font-mono text-foreground mt-1">{formatINR(baseline.recovered_paise / 100)}</div>
          <div className="text-xs text-muted-foreground mt-1">{baseline.recovery_rate}% Recovery Rate</div>
        </div>

        <div className="p-4 rounded-lg border border-border bg-card">
          <div className="text-xs font-medium text-muted-foreground">Nirnay Recovery</div>
          <div className="text-xl font-bold font-mono text-emerald-500 mt-1">{formatINR(nirnay.recovered_paise / 100)}</div>
          <div className="text-xs text-emerald-500/80 mt-1">{nirnay.recovery_rate}% Recovery Rate</div>
        </div>

        <div className="p-4 rounded-lg border border-border bg-card">
          <div className="text-xs font-medium text-muted-foreground">Incremental Recovery</div>
          <div className={`text-xl font-bold font-mono mt-1 ${isPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
            {isPositive ? '+' : ''}{formatINR(incRupees)}
          </div>
          <div className="text-xs text-muted-foreground mt-1">Unclipped Net Impact</div>
        </div>

        <div className="p-4 rounded-lg border border-border bg-card">
          <div className="text-xs font-medium text-muted-foreground">Relative Uplift</div>
          <div className="text-xl font-bold font-mono text-indigo-400 mt-1">+{evalData.relative_uplift_pct}%</div>
          <div className="text-xs text-muted-foreground mt-1">30 Held-Out Cases</div>
        </div>
      </div>
    </div>
  );
}
