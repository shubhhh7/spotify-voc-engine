"use client";

import { cn } from "@/lib/utils";

interface SourceBadgeProps {
  source: string;
}

const SOURCE_COLORS: Record<string, string> = {
  reddit: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  app_store: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  play_store: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  spotify_community: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  social: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  hackernews: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  lemmy: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400",
};

const SOURCE_LABELS: Record<string, string> = {
  reddit: "Reddit",
  app_store: "App Store",
  play_store: "Play Store",
  spotify_community: "Community",
  social: "Social",
  hackernews: "Hacker News",
  lemmy: "Lemmy",
};

export function SourceBadge({ source }: SourceBadgeProps) {
  const colorClass = SOURCE_COLORS[source] || "bg-muted text-muted-foreground";
  const label = SOURCE_LABELS[source] || source.replace(/_/g, " ");

  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize", colorClass)}>
      {label}
    </span>
  );
}
