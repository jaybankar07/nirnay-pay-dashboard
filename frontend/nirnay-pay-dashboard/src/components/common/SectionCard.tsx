import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface SectionCardProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  contentClassName?: string;
}

export const SectionCard: React.FC<SectionCardProps> = ({
  title,
  description,
  action,
  children,
  className,
  contentClassName,
}) => {
  return (
    <Card className={cn("border border-border/80 bg-card shadow-xs", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-4 space-y-0 border-b border-border/40">
        <div>
          <CardTitle className="text-base font-semibold tracking-tight text-foreground">{title}</CardTitle>
          {description && <CardDescription className="text-xs text-muted-foreground mt-0.5">{description}</CardDescription>}
        </div>
        {action && <div>{action}</div>}
      </CardHeader>
      <CardContent className={cn("pt-4", contentClassName)}>{children}</CardContent>
    </Card>
  );
};
