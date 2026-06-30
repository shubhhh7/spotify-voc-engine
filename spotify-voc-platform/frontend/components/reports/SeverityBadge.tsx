"use client";

import { cn } from "@/lib/utils";

interface SeverityBadgeProps {
  level: number;
}

function getLabel(level: number): string {
  if (level >= 5) return "Critical";
  if (level >= 4) return "High";
  if (level >= 2) return "Medium";
  return "Low";
}

export function SeverityBadge({ level }: SeverityBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        level >= 4 && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
        level >= 2 && level < 4 && "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
        level < 2 && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
      )}
    >
      {getLabel(level)}
    </span>
  );
}
