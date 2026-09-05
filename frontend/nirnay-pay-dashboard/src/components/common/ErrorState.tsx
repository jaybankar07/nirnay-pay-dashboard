import React from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle, RotateCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Failed to load data",
  message = "The recovery service is temporarily unavailable. Please try again.",
  onRetry,
  className,
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-center rounded-lg border border-destructive/20 bg-destructive/5 text-destructive dark:bg-destructive/10", className)}>
      <AlertCircle className="w-9 h-9 mb-2 text-destructive" />
      <h3 className="text-sm font-semibold tracking-tight">{title}</h3>
      <p className="mt-1 text-xs text-muted-foreground max-w-md">{message}</p>
      {onRetry && (
        <Button size="sm" variant="outline" className="mt-4 text-xs font-medium border-destructive/30 hover:bg-destructive/10" onClick={onRetry}>
          <RotateCw className="w-3.5 h-3.5 mr-1.5" />
          Retry Request
        </Button>
      )}
    </div>
  );
};
