"use client";

import { TrendingUp } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { EmptyState } from "./EmptyState";
import { cn } from "@/lib/utils";
import type { EmergingTrend } from "./types";

interface Props {
  content: { trends?: EmergingTrend[]; watch_list?: EmergingTrend[] } | null;
}

const IMPACT_STYLES = {
  High: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  Medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  Low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

export function EmergingTrendsSection({ content }: Props) {
  const trends = content?.trends;

  if (!trends || trends.length === 0) {
    return <EmptyState icon={TrendingUp} title="No emerging trends identified" description="Generate emerging trends analysis to see what's changing." />;
  }

  const sorted = [...trends].sort((a, b) => {
    const order = { High: 0, Medium: 1, Low: 2 };
    return (order[a.potential_impact] ?? 2) - (order[b.potential_impact] ?? 2);
  });

  return (
    <section className="space-y-6">
      <SectionHeader title="Emerging Trends" icon={TrendingUp} description="Growth signals and shifting user behavior" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sorted.map((trend, i) => (
          <div key={i} className="rounded-lg border border-border bg-card p-5 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-sm font-semibold text-foreground">{trend.name}</h4>
              <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", IMPACT_STYLES[trend.potential_impact] || IMPACT_STYLES.Low)}>
                {trend.potential_impact}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{trend.description}</p>
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {trend.growth_signal}
              </span>
              <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {trend.time_horizon}
              </span>
            </div>
            <ConfidenceBadge score={trend.confidence} />
          </div>
        ))}
      </div>

      {/* Watch List */}
      {content?.watch_list && content.watch_list.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground">Watch List</h4>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {content.watch_list.map((item, i) => (
              <div key={i} className="rounded-lg border border-border bg-muted/30 p-4 space-y-1 opacity-75">
                <h5 className="text-xs font-medium text-foreground">{item.name}</h5>
                <p className="text-xs text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
