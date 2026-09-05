import React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { CheckCircle2, ShieldAlert, XCircle, AlertTriangle, Clock, Activity, Zap } from "lucide-react";

export type StatusVariant =
  | "APPROVED"
  | "BLOCKED"
  | "STOPPED"
  | "SUCCESS"
  | "FAILED"
  | "PENDING"
  | "DETECTED"
  | "DIAGNOSED"
  | "IN_PROGRESS"
  | "IN_REVIEW"
  | "EXECUTED"
  | "RECOVERED"
  | "HUMAN_REVIEW"
  | string;

interface StatusBadgeProps {
  status: StatusVariant;
  className?: string;
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className, showIcon = true }) => {
  const normalized = (status || "").toUpperCase();

  let badgeStyle = "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200 border-slate-200";
  let icon = <Activity className="w-3 h-3 mr-1" />;

  switch (normalized) {
    case "APPROVED":
    case "RECOVERED":
    case "SUCCESS":
      badgeStyle = "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800";
      icon = <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600 dark:text-emerald-400" />;
      break;

    case "BLOCKED":
      badgeStyle = "bg-amber-50 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300 border-amber-200 dark:border-amber-800";
      icon = <ShieldAlert className="w-3 h-3 mr-1 text-amber-600 dark:text-amber-400" />;
      break;

    case "STOPPED":
    case "FAILED":
      badgeStyle = "bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border-rose-200 dark:border-rose-800";
      icon = <XCircle className="w-3 h-3 mr-1 text-rose-600 dark:text-rose-400" />;
      break;

    case "DETECTED":
    case "DIAGNOSED":
    case "PENDING":
    case "IN_PROGRESS":
      badgeStyle = "bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300 border-sky-200 dark:border-sky-800";
      icon = <Clock className="w-3 h-3 mr-1 text-sky-600 dark:text-sky-400" />;
      break;

    case "HUMAN_REVIEW":
    case "IN_REVIEW":
      badgeStyle = "bg-purple-50 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300 border-purple-200 dark:border-purple-800";
      icon = <AlertTriangle className="w-3 h-3 mr-1 text-purple-600 dark:text-purple-400" />;
      break;

    case "EXECUTED":
      badgeStyle = "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800";
      icon = <Zap className="w-3 h-3 mr-1 text-indigo-600 dark:text-indigo-400" />;
      break;
  }

  return (
    <Badge
      variant="outline"
      className={cn("inline-flex items-center px-2.5 py-0.5 text-xs font-semibold rounded-md border tracking-tight transition-colors", badgeStyle, className)}
    >
      {showIcon && icon}
      {normalized}
    </Badge>
  );
};
