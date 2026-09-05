import React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  rows?: number;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ rows = 4, className }) => {
  return (
    <div className={cn("space-y-3 p-4", className)}>
      <Skeleton className="h-6 w-1/3 rounded-md" />
      <div className="space-y-2 pt-2">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-md" />
        ))}
      </div>
    </div>
  );
};
