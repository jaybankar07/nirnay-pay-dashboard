import React from "react";
import { formatDateTime } from "@/lib/format";
import { CheckCircle2, ShieldAlert, AlertTriangle, Activity, User, Bot, Server } from "lucide-react";
import type { AuditEvent } from "@/types/api";

interface TimelineProps {
  events: AuditEvent[];
}

export const Timeline: React.FC<TimelineProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return <p className="text-xs text-muted-foreground text-center py-4">No audit events recorded.</p>;
  }

  const getActorIcon = (actor: string) => {
    const act = (actor || "").toUpperCase();
    if (act.includes("AI")) return <Bot className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />;
    if (act.includes("SYSTEM") || act.includes("RULE")) return <Server className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />;
    return <User className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />;
  };

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border/60">
      {events.map((evt, idx) => (
        <div key={evt.event_id || idx} className="relative group">
          <div className="absolute -left-6 top-0.5 flex items-center justify-center w-5 h-5 rounded-full bg-background border border-border shadow-2xs group-hover:border-primary transition-colors">
            {getActorIcon(evt.actor)}
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
            <h4 className="text-xs font-semibold text-foreground tracking-tight">{evt.description || evt.event_type}</h4>
            <span className="text-[11px] font-mono text-muted-foreground tabular-nums">{formatDateTime(evt.timestamp)}</span>
          </div>
          <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
            <span className="inline-flex items-center font-medium text-foreground/80 bg-muted/50 px-1.5 py-0.5 rounded-xs border border-border/40">
              Actor: {evt.actor}
            </span>
            <span className="font-mono text-muted-foreground">ID: {evt.event_id}</span>
          </div>
          {evt.details && Object.keys(evt.details).length > 0 && (
            <pre className="mt-2 text-[11px] font-mono bg-muted/40 p-2 rounded border border-border/40 overflow-x-auto text-foreground/80">
              {JSON.stringify(evt.details, null, 2)}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
};
