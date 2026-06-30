"use client";

import { useState } from "react";
import { Layers, ChevronDown, ChevronRight } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { EmptyState } from "./EmptyState";
import { cn } from "@/lib/utils";
import type { ThemeClusteringContent } from "./types";

interface Props {
  content: ThemeClusteringContent | null;
}

function sentimentColor(mix: string) {
  const lower = mix?.toLowerCase() || "";
  if (lower.includes("positive")) return "text-green-600 dark:text-green-400";
  if (lower.includes("negative")) return "text-red-600 dark:text-red-400";
  return "text-amber-600 dark:text-amber-400";
}

export function ThemeClustersSection({ content }: Props) {
  const clusters = content?.clusters;

  if (!clusters || clusters.length === 0) {
    return <EmptyState icon={Layers} title="No theme clusters identified" description="Generate theme clustering to see how feedback groups together." />;
  }

  const sorted = [...clusters].sort((a, b) => b.review_count - a.review_count);

  return (
    <section className="space-y-6">
      <SectionHeader title="Theme Clusters" icon={Layers} description="How feedback naturally groups into topic areas" />

      {/* Cross-cutting themes */}
      {content?.cross_cutting_themes && content.cross_cutting_themes.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Cross-cutting Themes</h4>
          <div className="flex flex-wrap gap-2">
            {content.cross_cutting_themes.map((theme, i) => (
              <span key={i} className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                {theme}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {sorted.map((cluster, i) => (
          <ClusterCard key={i} cluster={cluster} />
        ))}
      </div>
    </section>
  );
}

function ClusterCard({ cluster }: { cluster: ThemeClusteringContent["clusters"][0] }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-border bg-card p-5 space-y-3">
      <div className="flex items-start justify-between">
        <h4 className="text-sm font-semibold text-foreground">{cluster.theme}</h4>
        <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {cluster.review_count} reviews
        </span>
      </div>

      <div className="flex items-center gap-2">
        <span className={cn("text-xs font-medium", sentimentColor(cluster.sentiment_mix))}>
          {cluster.sentiment_mix}
        </span>
      </div>

      <p className="text-sm text-muted-foreground">{cluster.key_insight}</p>

      {/* Sub-themes as chips */}
      {cluster.sub_themes && cluster.sub_themes.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {cluster.sub_themes.slice(0, 8).map((sub, i) => (
            <span key={i} className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {sub}
            </span>
          ))}
        </div>
      )}

      {/* Expandable quotes */}
      {cluster.representative_quotes && cluster.representative_quotes.length > 0 && (
        <div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            {cluster.representative_quotes.length} quotes
          </button>
          {expanded && (
            <div className="mt-2 space-y-2">
              {cluster.representative_quotes.slice(0, 3).map((q, i) => (
                <blockquote key={i} className="border-l-2 border-muted-foreground/20 pl-3 text-xs italic text-muted-foreground">
                  &ldquo;{q}&rdquo;
                </blockquote>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
