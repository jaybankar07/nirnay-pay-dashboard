import React from "react";
import { useHealthQuery } from "@/lib/api/queries";
import { isUseFixtures, setUseFixtures } from "@/lib/api/config";
import { Activity, Server, Radio } from "lucide-react";
import { toast } from "sonner";

export const HealthIndicator: React.FC = () => {
  const { data: health, isError, isLoading } = useHealthQuery();
  const useFixtures = isUseFixtures();

  const handleToggle = () => {
    const nextMode = !useFixtures;
    setUseFixtures(nextMode);
    toast.info(nextMode ? "Switched to Demo Fixture Mode" : "Switched to Live FastAPI Backend Mode");
  };

  if (useFixtures) {
    return (
      <button
        type="button"
        onClick={handleToggle}
        title="Click to toggle to Live FastAPI Backend Mode"
        className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-900 dark:bg-amber-950/80 dark:text-amber-200 border border-amber-300 dark:border-amber-700 hover:bg-amber-200 dark:hover:bg-amber-900 transition-all shadow-xs cursor-pointer"
      >
        <Server className="w-3.5 h-3.5 text-amber-700 dark:text-amber-300" />
        <span>Fixture Mode</span>
        <span className="text-[10px] opacity-75 font-mono">(Click for Live API)</span>
      </button>
    );
  }

  if (isLoading) {
    return (
      <button
        type="button"
        disabled
        className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 animate-pulse border border-slate-200 dark:border-slate-700"
      >
        <Activity className="w-3.5 h-3.5" />
        <span>Connecting to Backend...</span>
      </button>
    );
  }

  const isHealthy = health?.status === "ok" || health?.status === "healthy";

  if (isError || !isHealthy) {
    return (
      <button
        type="button"
        onClick={handleToggle}
        title="Click to toggle back to Demo Fixture Mode"
        className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-200 border border-rose-300 dark:border-rose-700 hover:bg-rose-200 transition-all shadow-xs cursor-pointer"
      >
        <span className="w-2 h-2 rounded-full bg-rose-500"></span>
        <span>Live Backend (Offline)</span>
        <span className="text-[10px] opacity-75 font-mono">(Click for Fixtures)</span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      title="Click to toggle back to Demo Fixture Mode"
      className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-900 dark:bg-emerald-950/80 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700 hover:bg-emerald-200 transition-all shadow-xs cursor-pointer"
    >
      <Radio className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 animate-pulse" />
      <span>Live FastAPI Mode</span>
      <span className="text-[10px] opacity-75 font-mono">(Click for Fixtures)</span>
    </button>
  );
};
