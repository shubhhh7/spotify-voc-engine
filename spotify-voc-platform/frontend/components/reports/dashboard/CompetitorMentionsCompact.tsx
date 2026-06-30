"use client";

import { cn } from "@/lib/utils";
import type { CompetitorMentionsContent } from "../types";

interface Props {
  content: CompetitorMentionsContent | null;
}

const SENTIMENT_DOT = {
  Positive: "bg-green-500",
  Neutral: "bg-amber-500",
  Negative: "bg-red-500",
};

export function CompetitorMentionsCompact({ content }: Props) {
  const competitors = content?.competitors;

  if (!competitors || competitors.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No competitor mentions found.</p>
    );
  }

  const sorted = [...competitors].sort((a, b) => b.mention_count - a.mention_count);

  return (
    <div className="space-y-3">
      {/* Competitor rows */}
      <div className="space-y-1.5">
        {sorted.map((comp, i) => (
          <div
            key={i}
            className="flex items-center gap-3 p-2 rounded-md hover:bg-muted/50 transition-colors"
          >
            {/* Sentiment dot */}
            <span
              className={cn(
                "w-2.5 h-2.5 rounded-full shrink-0",
                SENTIMENT_DOT[comp.sentiment] || "bg-muted-foreground"
              )}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-foreground">
                  {comp.competitor}
                </span>
                <span className="text-xs text-muted-foreground">
                  {comp.mention_count} mentions
                </span>
              </div>
              {comp.perceived_advantage && (
                <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                  Advantage: {comp.perceived_advantage}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Spotify Advantages */}
      {content?.spotify_advantages && content.spotify_advantages.length > 0 && (
        <div className="pt-2 border-t border-border">
          <h4 className="text-xs font-semibold text-green-600 dark:text-green-400 mb-1">
            Spotify Strengths
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {content.spotify_advantages.slice(0, 4).map((adv, i) => (
              <span
                key={i}
                className="rounded-full bg-green-100 dark:bg-green-900/20 px-2 py-0.5 text-[10px] text-green-700 dark:text-green-400"
              >
                ✓ {adv}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
