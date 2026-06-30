"use client";

import { cn } from "@/lib/utils";

interface ConfidenceBadgeProps {
  score: number;
}

export function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        score >= 80 && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
        score >= 50 && score < 80 && "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
        score < 50 && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
      )}
    >
      {score}% confidence
    </span>
  );
}
