import React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout/AppLayout";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { SectionCard } from "@/components/common/SectionCard";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { useDashboardSummaryQuery } from "@/lib/api/queries";
import {
  formatINR,
  formatPercent,
  formatNumber,
  humanizeToken,
} from "@/lib/format";
import {
  DollarSign,
  TrendingUp,
  ShieldAlert,
  AlertTriangle,
  BarChart3,
  Layers,
  Sparkles,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";

export const Route = createFileRoute("/analytics")({
  component: AnalyticsPage,
});

function AnalyticsPage() {
  const { data: summary, isLoading, isError, refetch } = useDashboardSummaryQuery();

  if (isError) {
    return (
      <AppLayout>
        <PageHeader title="Analytics & Benchmarks" description="Nirnay Pay recovery impact vs baseline." />
        <ErrorState
          title="Failed to load analytics data"
          message="Could not connect to the recovery analytics service."
          onRetry={refetch}
        />
      </AppLayout>
    );
  }

  if (isLoading || !summary) {
    return (
      <AppLayout>
        <LoadingState rows={8} />
      </AppLayout>
    );
  }

  const baseline = summary.comparison?.baseline;
  const nirnay = summary.comparison?.nirnay_pay;

  const comparisonChartData = [
    {
      metric: "Recovery Rate (%)",
      Baseline: baseline ? baseline.recovery_rate * 100 : 0,
      "Nirnay Pay": nirnay ? nirnay.recovery_rate * 100 : 0,
    },
    {
      metric: "Compliance Blocks",
      Baseline: baseline?.compliance_blocks ?? 0,
      "Nirnay Pay": nirnay?.compliance_blocks ?? 0,
    },
    {
      metric: "Stopped Cases",
      Baseline: baseline?.stopped_cases ?? 0,
      "Nirnay Pay": nirnay?.stopped_cases ?? 0,
    },
  ];

  return (
    <AppLayout>
      <PageHeader
        title="Recovery Analytics & Impact"
        description="Comprehensive analytics comparing traditional baseline recovery against Nirnay Pay autonomous recovery."
      />

      {/* Top Level Metric Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Revenue Risk"
          value={formatINR(summary.revenue_at_risk)}
          subtitle="Identified across scenarios"
          icon={<DollarSign className="w-4 h-4 text-amber-600 dark:text-amber-400" />}
        />
        <StatCard
          title="Revenue Recovered"
          value={formatINR(summary.revenue_recovered)}
          subtitle="Settled & collected"
          icon={<TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />}
        />
        <StatCard
          title="Recovery Rate"
          value={formatPercent(summary.recovery_rate, 1)}
          subtitle="Overall system yield"
          icon={<BarChart3 className="w-4 h-4 text-sky-600 dark:text-sky-400" />}
        />
        <StatCard
          title="Compliance Blocks"
          value={formatNumber(summary.compliance_blocks)}
          subtitle="Customer protection rules"
          icon={<ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400" />}
        />
        <StatCard
          title="Stopped Cases"
          value={formatNumber(nirnay?.stopped_cases ?? 0)}
          subtitle="Diminishing returns cap"
          icon={<AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400" />}
        />
        <StatCard
          title="Total Pipeline Cases"
          value={formatNumber(nirnay?.total_cases ?? summary.active_cases)}
          subtitle="Engineered pipeline total"
          icon={<Layers className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />}
        />
      </div>

      {/* Baseline vs Nirnay Pay Benchmark Comparison */}
      <SectionCard
        title="Baseline vs. Nirnay Pay Benchmark"
        description="Side-by-side comparison of standard merchant recovery rules versus Nirnay Pay AI governance."
        action={
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/60 px-2.5 py-1 rounded border border-border/60">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            <span>DataSource: <strong className="text-foreground font-mono">{summary.comparison?.data_source || "REAL_PRODUCTION"}</strong></span>
          </div>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Comparison Table */}
          <div className="lg:col-span-1 space-y-4">
            <div className="p-4 rounded-md border border-border/60 bg-muted/30 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Traditional Baseline</h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Recovery Rate:</span>
                  <span className="font-mono font-bold">{formatPercent(baseline?.recovery_rate ?? 0, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Revenue Recovered:</span>
                  <span className="font-mono font-bold">{formatINR(baseline?.revenue_recovered ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Compliance Violations:</span>
                  <span className="font-mono font-bold text-amber-600">{baseline?.compliance_blocks ?? 0}</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-md border border-emerald-500/30 bg-emerald-50/20 dark:bg-emerald-950/20 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">Nirnay Pay RecoveryOS</h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Recovery Rate:</span>
                  <span className="font-mono font-bold text-emerald-600">{formatPercent(nirnay?.recovery_rate ?? 0, 1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Revenue Recovered:</span>
                  <span className="font-mono font-bold text-emerald-600">{formatINR(nirnay?.revenue_recovered ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Protected Blocks:</span>
                  <span className="font-mono font-bold text-emerald-600">{nirnay?.compliance_blocks ?? 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Benchmark Bar Chart */}
          <div className="lg:col-span-2 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-border/40" />
                <XAxis dataKey="metric" stroke="currentColor" className="text-xs text-muted-foreground" />
                <YAxis stroke="currentColor" className="text-xs text-muted-foreground" />
                <Tooltip contentStyle={{ backgroundColor: "var(--color-card)", borderColor: "var(--color-border)", borderRadius: "6px" }} />
                <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "12px" }} />
                <Bar dataKey="Baseline" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Nirnay Pay" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </SectionCard>

      {/* Scenario Yield & Recovery Performance */}
      <SectionCard title="Scenario Recovery Yield" description="Recovery performance broken down by failure scenario type">
        {summary.scenario_breakdown && summary.scenario_breakdown.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {summary.scenario_breakdown.map((s) => (
              <div key={s.scenario} className="p-4 rounded-md border border-border/60 bg-card space-y-2">
                <div className="text-xs font-bold text-foreground">{humanizeToken(s.scenario)}</div>
                <div className="flex justify-between items-baseline pt-1">
                  <span className="text-[11px] text-muted-foreground">Cases:</span>
                  <span className="font-mono text-xs font-semibold">{s.cases}</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span className="text-[11px] text-muted-foreground">Risk:</span>
                  <span className="font-mono text-xs font-bold text-amber-600">{formatINR(s.amount_at_risk)}</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span className="text-[11px] text-muted-foreground">Recovered:</span>
                  <span className="font-mono text-xs font-bold text-emerald-600">{formatINR(s.amount_recovered)}</span>
                </div>
                <div className="flex justify-between items-baseline pt-1 border-t border-border/40">
                  <span className="text-[11px] font-semibold text-muted-foreground">Yield:</span>
                  <span className="font-mono text-xs font-extrabold text-foreground">{formatPercent(s.recovery_rate, 1)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No scenario analytics" description="Scenario breakdown is currently empty." />
        )}
      </SectionCard>
    </AppLayout>
  );
}
