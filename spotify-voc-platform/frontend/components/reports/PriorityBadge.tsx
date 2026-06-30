"use client";

import { cn } from "@/lib/utils";

interface PriorityBadgeProps {
  priority: "High" | "Medium" | "Low";
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        priority === "High" && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
        priority === "Medium" && "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
        priority === "Low" && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
      )}
    >
      {priority} Priority
    </span>
  );
}
