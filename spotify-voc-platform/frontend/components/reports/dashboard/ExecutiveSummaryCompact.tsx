"use client";

import { cn } from "@/lib/utils";
import { SeverityBadge } from "../SeverityBadge";
import { ConfidenceBadge } from "../ConfidenceBadge";
import type { ExecutiveSummaryContent } from "../types";

interface Props {
  content: ExecutiveSummaryContent | null;
}

export function ExecutiveSummaryCompact({ content }: Props) {
  if (!content) {
    return (
      <p className="text-sm text-muted-foreground">No executive summary available.</p>
    );
  }

  return (
    <div className="space-y-3">
      {/* Bottom line — concise headline */}
      <p className="text-sm font-medium text-foreground leading-relaxed">
        {content.bottom_line}
      </p>

      {/* Meta badges */}
      <div className="flex flex-wrap items-center gap-2">
        <SentimentPill sentiment={content.overall_sentiment} />
        <ConfidenceBadge score={content.confidence_score} />
        {content.key_metric && (
          <span className="rounded-md bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
            {content.key_metric}
          </span>
        )}
      </div>

      {/* Key findings as bullet list — max 5 */}
      {content.key_findings && content.key_findings.length > 0 && (
        <div className="space-y-1.5 pt-1">
          {content.key_findings.slice(0, 5).map((finding, i) => (
            <div
              key={i}
              className="flex items-center gap-2 text-xs"
            >
              <SeverityBadge level={finding.severity} />
              <span className="font-medium text-foreground truncate">{finding.theme}</span>
              <span className="text-muted-foreground hidden sm:inline">— {finding.description}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SentimentPill({ sentiment }: { sentiment: string }) {
  const s = sentiment?.toLowerCase();
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        s === "positive" && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
        s === "negative" && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
        (s === "mixed" || s === "neutral") && "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
      )}
    >
      {sentiment}
    </span>
  );
}
