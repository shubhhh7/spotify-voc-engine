"use client";

import { cn } from "@/lib/utils";

interface ProgressIndicatorProps {
  value: number;
  max: number;
  label?: string;
  color?: "default" | "green" | "amber" | "red";
}

export function ProgressIndicator({ value, max, label, color = "default" }: ProgressIndicatorProps) {
  const percentage = Math.round((value / max) * 100);

  return (
    <div className="flex items-center gap-3">
      {label && <span className="text-xs text-muted-foreground w-20 shrink-0">{label}</span>}
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            color === "green" && "bg-green-500",
            color === "amber" && "bg-amber-500",
            color === "red" && "bg-red-500",
            color === "default" && "bg-primary"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium text-foreground w-8 text-right">{value}</span>
    </div>
  );
}
