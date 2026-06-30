"use client";

import { cn } from "@/lib/utils";
import type { ThemeClusteringContent } from "../types";

interface Props {
  content: ThemeClusteringContent | null;
}

function sentimentColor(mix: string) {
  const lower = mix?.toLowerCase() || "";
  if (lower.includes("positive")) return "text-green-600 dark:text-green-400";
  if (lower.includes("negative")) return "text-red-600 dark:text-red-400";
  return "text-amber-600 dark:text-amber-400";
}

export function ThemeClustersCompact({ content }: Props) {
  const clusters = content?.clusters;

  if (!clusters || clusters.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No theme clusters identified.</p>
    );
  }

  const sorted = [...clusters].sort((a, b) => b.review_count - a.review_count);

  return (
    <div className="space-y-3">
      {/* Cross-cutting themes as chips */}
      {content?.cross_cutting_themes && content.cross_cutting_themes.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {content.cross_cutting_themes.map((theme, i) => (
            <span
              key={i}
              className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
            >
              {theme}
            </span>
          ))}
        </div>
      )}

      {/* Cluster list */}
      <div className="space-y-1.5">
        {sorted.map((cluster, i) => (
          <div
            key={i}
            className="flex items-center gap-3 p-2 rounded-md hover:bg-muted/50 transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-foreground truncate">
                  {cluster.theme}
                </span>
                <span className={cn("text-[10px] font-medium", sentimentColor(cluster.sentiment_mix))}>
                  {cluster.sentiment_mix}
                </span>
              </div>
              {cluster.sub_themes && cluster.sub_themes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {cluster.sub_themes.slice(0, 4).map((sub, j) => (
                    <span
                      key={j}
                      className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                    >
                      {sub}
                    </span>
                  ))}
                  {cluster.sub_themes.length > 4 && (
                    <span className="text-[10px] text-muted-foreground">
                      +{cluster.sub_themes.length - 4}
                    </span>
                  )}
                </div>
              )}
            </div>
            <span className="text-xs font-medium text-muted-foreground shrink-0">
              {cluster.review_count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
