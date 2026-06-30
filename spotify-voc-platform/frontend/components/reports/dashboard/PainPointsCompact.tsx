"use client";

import { SeverityBadge } from "../SeverityBadge";
import type { PainPoint } from "../types";

interface Props {
  content: { pain_points?: PainPoint[] } | null;
}

export function PainPointsCompact({ content }: Props) {
  const painPoints = content?.pain_points;

  if (!painPoints || painPoints.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No pain points identified.</p>
    );
  }

  const sorted = [...painPoints].sort((a, b) => {
    const scoreA = a.severity * a.frequency;
    const scoreB = b.severity * b.frequency;
    return scoreB - scoreA;
  });

  return (
    <div className="space-y-2">
      {sorted.map((point, i) => (
        <div
          key={i}
          className="flex items-start gap-3 p-2 rounded-md hover:bg-muted/50 transition-colors"
        >
          {/* Rank */}
          <span className="text-xs font-bold text-muted-foreground w-5 shrink-0 pt-0.5">
            #{i + 1}
          </span>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground truncate">
                {point.title}
              </span>
              <SeverityBadge level={point.severity} />
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-muted-foreground">
                {point.frequency} mentions
              </span>
              {point.category && (
                <span className="text-xs text-muted-foreground">
                  • {point.category}
                </span>
              )}
            </div>
          </div>

          {/* Priority score visual */}
          <div className="shrink-0 flex flex-col items-center">
            <span className="text-xs font-bold text-foreground">
              {Math.round(point.severity * point.frequency)}
            </span>
            <span className="text-[10px] text-muted-foreground">score</span>
          </div>
        </div>
      ))}
    </div>
  );
}
