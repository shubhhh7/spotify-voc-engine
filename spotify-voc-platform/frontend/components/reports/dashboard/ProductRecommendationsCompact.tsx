"use client";

import { ProgressIndicator } from "../ProgressIndicator";
import { cn } from "@/lib/utils";
import type { ProductRecommendationsContent, ProductRecommendation } from "../types";

interface Props {
  content: ProductRecommendationsContent | null;
}

export function ProductRecommendationsCompact({ content }: Props) {
  const recs = content?.recommendations;

  if (!recs || recs.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No recommendations generated.</p>
    );
  }

  // Use quick_wins + strategic_bets if available, otherwise sorted recs
  const quickWins = content?.quick_wins || [];
  const strategicBets = content?.strategic_bets || [];
  const hasCategories = quickWins.length > 0 || strategicBets.length > 0;

  const sorted = hasCategories
    ? [...quickWins, ...strategicBets]
    : [...recs].sort((a, b) => (b.ice_score || 0) - (a.ice_score || 0));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {sorted.slice(0, 6).map((rec, i) => {
        const isQuickWin = quickWins.includes(rec);
        return (
          <RecCard key={i} rec={rec} accent={isQuickWin ? "border-l-green-500" : "border-l-primary"} />
        );
      })}
    </div>
  );
}

function RecCard({ rec, accent }: { rec: ProductRecommendation; accent: string }) {
  const impact = Number(rec.impact_score) || 0;
  const effort = Number(rec.effort_score) || 0;
  const confidence = Number(rec.confidence_score) || 0;
  const rawIce = Number(rec.ice_score) || 0;
  const iceScore = rawIce > 0 ? rawIce : Math.round((impact * confidence) / Math.max(effort, 1));

  return (
    <div className={cn("rounded-md border border-border p-3 border-l-4 space-y-2", accent)}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-xs font-semibold text-foreground line-clamp-1">{rec.title}</h4>
        <span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-primary">
          ICE {iceScore}
        </span>
      </div>

      {/* Score bars — compact */}
      <div className="space-y-1">
        <ProgressIndicator label="Impact" value={rec.impact_score} max={10} color="green" />
        <ProgressIndicator label="Effort" value={rec.effort_score} max={10} color="amber" />
        <ProgressIndicator label="Confidence" value={rec.confidence_score} max={10} color="default" />
      </div>

      {/* Personas */}
      {rec.affected_personas && rec.affected_personas.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {rec.affected_personas.slice(0, 2).map((p, i) => (
            <span
              key={i}
              className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
            >
              {p}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
