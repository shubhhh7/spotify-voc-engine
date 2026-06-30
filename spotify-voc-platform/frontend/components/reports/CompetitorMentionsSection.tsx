"use client";

import { Swords } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { EmptyState } from "./EmptyState";
import { cn } from "@/lib/utils";
import type { CompetitorMentionsContent } from "./types";

interface Props {
  content: CompetitorMentionsContent | null;
}

const SENTIMENT_STYLES = {
  Positive: "text-green-600 dark:text-green-400",
  Neutral: "text-amber-600 dark:text-amber-400",
  Negative: "text-red-600 dark:text-red-400",
};

export function CompetitorMentionsSection({ content }: Props) {
  const competitors = content?.competitors;

  if (!competitors || competitors.length === 0) {
    return <EmptyState icon={Swords} title="No competitor mentions found" description="Generate competitor analysis to see competitive positioning." />;
  }

  const sorted = [...competitors].sort((a, b) => b.mention_count - a.mention_count);

  return (
    <section className="space-y-6">
      <SectionHeader title="Competitor Mentions" icon={Swords} description="How users compare Spotify to alternatives" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sorted.map((comp, i) => (
          <div key={i} className="rounded-lg border border-border bg-card p-5 space-y-3">
            <div className="flex items-start justify-between">
              <h4 className="text-sm font-semibold text-foreground">{comp.competitor}</h4>
              <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                {comp.mention_count} mentions
              </span>
            </div>
            <span className={cn("text-xs font-medium", SENTIMENT_STYLES[comp.sentiment] || "text-muted-foreground")}>
              {comp.sentiment} sentiment
            </span>
            <p className="text-sm text-muted-foreground">{comp.context}</p>
            {comp.perceived_advantage && (
              <div className="rounded-md bg-muted/50 px-3 py-2">
                <span className="text-xs font-medium text-muted-foreground">Perceived advantage: </span>
                <span className="text-xs text-foreground">{comp.perceived_advantage}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Switching Signals */}
      {content?.switching_signals && content.switching_signals.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-muted-foreground">Switching Signals</h4>
          <div className="grid gap-3 md:grid-cols-2">
            {content.switching_signals.map((signal, i) => (
              <div key={i} className="rounded-md border border-red-200 dark:border-red-900/30 bg-red-50/30 dark:bg-red-900/5 p-3 space-y-1">
                <p className="text-sm text-foreground">{signal.signal}</p>
                <p className="text-xs text-muted-foreground">
                  → {signal.target_competitor} • {signal.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Spotify Advantages */}
      {content?.spotify_advantages && content.spotify_advantages.length > 0 && (
        <div className="rounded-lg border border-green-200 dark:border-green-900/30 bg-green-50/30 dark:bg-green-900/5 p-4">
          <h4 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Spotify Strengths</h4>
          <ul className="space-y-1">
            {content.spotify_advantages.map((adv, i) => (
              <li key={i} className="text-sm text-foreground flex items-start gap-2">
                <span className="text-green-500">✓</span> {adv}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
