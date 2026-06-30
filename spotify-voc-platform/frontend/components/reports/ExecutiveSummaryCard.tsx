"use client";

import { cn } from "@/lib/utils";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { SeverityBadge } from "./SeverityBadge";
import { EmptyState } from "./EmptyState";
import { FileText } from "lucide-react";
import type { ExecutiveSummaryContent } from "./types";

interface Props {
  content: ExecutiveSummaryContent | null;
}

function SentimentPill({ sentiment }: { sentiment: string }) {
  const s = sentiment?.toLowerCase();
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-sm font-medium",
        s === "positive" && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
        s === "negative" && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
        (s === "mixed" || s === "neutral") && "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
      )}
    >
      {sentiment}
    </span>
  );
}

export function ExecutiveSummaryCard({ content }: Props) {
  if (!content) {
    return <EmptyState icon={FileText} title="No executive summary generated" description="Generate insights to see your executive summary here." />;
  }

  return (
    <div className="rounded-xl border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent p-6 space-y-4">
      {/* Bottom Line */}
      <p className="text-lg font-medium text-foreground leading-relaxed">
        {content.bottom_line}
      </p>

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-3">
        <SentimentPill sentiment={content.overall_sentiment} />
        <ConfidenceBadge score={content.confidence_score} />
        {content.key_metric && (
          <span className="inline-flex items-center rounded-lg bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
            {content.key_metric}
          </span>
        )}
      </div>

      {/* Key Findings */}
      {content.key_findings && content.key_findings.length > 0 && (
        <div className="pt-2 space-y-2">
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Key Findings</h4>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {content.key_findings.slice(0, 5).map((finding, i) => (
              <div key={i} className="rounded-lg border border-border bg-card p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">{finding.theme}</span>
                  <SeverityBadge level={finding.severity} />
                </div>
                <p className="text-xs text-muted-foreground">{finding.description}</p>
                <span className="text-xs text-muted-foreground">Frequency: {finding.frequency}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
