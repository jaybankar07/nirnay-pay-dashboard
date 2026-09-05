import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
    isNegative?: boolean;
  };
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  className,
}) => {
  return (
    <Card className={cn("border border-border/80 bg-card shadow-xs transition-all hover:border-border", className)}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{title}</p>
          {icon && <div className="text-muted-foreground/70">{icon}</div>}
        </div>
        <div className="mt-3 flex items-baseline justify-between">
          <h3 className="font-mono text-2xl font-bold tracking-tight text-foreground tabular-nums">
            {value}
          </h3>
          {trend && (
            <span
              className={cn(
                "inline-flex items-center text-xs font-semibold px-1.5 py-0.5 rounded-xs",
                trend.isPositive && "text-emerald-700 bg-emerald-50 dark:bg-emerald-950/50 dark:text-emerald-300",
                trend.isNegative && "text-rose-700 bg-rose-50 dark:bg-rose-950/50 dark:text-rose-300",
                !trend.isPositive && !trend.isNegative && "text-muted-foreground bg-muted"
              )}
            >
              {trend.value}
            </span>
          )}
        </div>
        {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
      </CardContent>
    </Card>
  );
};
