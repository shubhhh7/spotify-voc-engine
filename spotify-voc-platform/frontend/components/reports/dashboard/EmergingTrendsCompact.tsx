"use client";

import { cn } from "@/lib/utils";
import { ConfidenceBadge } from "../ConfidenceBadge";
import type { EmergingTrend } from "../types";

interface Props {
  content: { trends?: EmergingTrend[]; watch_list?: EmergingTrend[] } | null;
}

const IMPACT_STYLES = {
  High: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  Medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  Low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

export function EmergingTrendsCompact({ content }: Props) {
  const trends = content?.trends;

  if (!trends || trends.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No emerging trends identified.</p>
    );
  }

  const sorted = [...trends].sort((a, b) => {
    const order = { High: 0, Medium: 1, Low: 2 };
    return (order[a.potential_impact] ?? 2) - (order[b.potential_impact] ?? 2);
  });

  return (
    <div className="space-y-2">
      {sorted.map((trend, i) => (
        <div
          key={i}
          className="p-2.5 rounded-md border border-border hover:bg-muted/30 transition-colors"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-medium text-foreground truncate">
              {trend.name}
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-medium shrink-0",
                IMPACT_STYLES[trend.potential_impact] || IMPACT_STYLES.Low
              )}
            >
              {trend.potential_impact}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
            {trend.description}
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-[10px] rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
              {trend.growth_signal}
            </span>
            <span className="text-[10px] rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
              {trend.time_horizon}
            </span>
            <ConfidenceBadge score={trend.confidence} />
          </div>
        </div>
      ))}
    </div>
  );
}
