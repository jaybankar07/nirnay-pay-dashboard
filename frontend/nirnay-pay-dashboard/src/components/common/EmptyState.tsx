import React from "react";
import { Button } from "@/components/ui/button";
import { FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No data found",
  description = "There are no records to display at this time.",
  icon = <FolderOpen className="w-10 h-10 text-muted-foreground/50" />,
  actionLabel,
  onAction,
  className,
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-center rounded-lg border border-dashed border-border bg-muted/20", className)}>
      <div className="mb-3 rounded-full bg-background p-3 shadow-2xs border border-border/50">{icon}</div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-xs text-muted-foreground max-w-sm">{description}</p>
      {actionLabel && onAction && (
        <Button size="sm" variant="outline" className="mt-4 text-xs font-medium" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
