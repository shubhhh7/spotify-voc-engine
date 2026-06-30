"use client";

import { AlertTriangle } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { SeverityBadge } from "./SeverityBadge";
import { EmptyState } from "./EmptyState";
import type { PainPoint } from "./types";

interface Props {
  content: { pain_points?: PainPoint[] } | null;
}

export function PainPointsSection({ content }: Props) {
  const painPoints = content?.pain_points;

  if (!painPoints || painPoints.length === 0) {
    return <EmptyState icon={AlertTriangle} title="No pain points identified" description="Generate pain points analysis to see user frustrations." />;
  }

  // Sort by severity × frequency descending
  const sorted = [...painPoints].sort((a, b) => {
    const scoreA = a.severity * a.frequency;
    const scoreB = b.severity * b.frequency;
    if (scoreB !== scoreA) return scoreB - scoreA;
    return b.severity - a.severity;
  });

  return (
    <section className="space-y-6">
      <SectionHeader title="Pain Points" icon={AlertTriangle} description="Top user frustrations ranked by severity and frequency" />

      <div className="grid gap-4 md:grid-cols-2">
        {sorted.map((point, i) => (
          <div key={i} className="rounded-lg border border-border bg-card p-5 space-y-3">
            {/* Header */}
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-sm font-semibold text-foreground">{point.title}</h4>
              <SeverityBadge level={point.severity} />
            </div>

            {/* Meta */}
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {point.frequency} mentions
              </span>
              {point.category && (
                <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  {point.category}
                </span>
              )}
            </div>

            {/* Explanation */}
            <p className="text-sm text-muted-foreground leading-relaxed">{point.explanation}</p>

            {/* Quote */}
            {point.representative_quotes && point.representative_quotes.length > 0 && (
              <blockquote className="border-l-2 border-primary/30 pl-3 text-xs italic text-muted-foreground">
                &ldquo;{point.representative_quotes[0]}&rdquo;
              </blockquote>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
