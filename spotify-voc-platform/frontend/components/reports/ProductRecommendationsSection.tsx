"use client";

import { Rocket } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { ProgressIndicator } from "./ProgressIndicator";
import { EmptyState } from "./EmptyState";
import { cn } from "@/lib/utils";
import type { ProductRecommendationsContent, ProductRecommendation } from "./types";

interface Props {
  content: ProductRecommendationsContent | null;
}

export function ProductRecommendationsSection({ content }: Props) {
  const recs = content?.recommendations;

  if (!recs || recs.length === 0) {
    return <EmptyState icon={Rocket} title="No product recommendations generated" description="Generate recommendations to get actionable roadmap items." />;
  }

  const sorted = [...recs].sort((a, b) => (b.ice_score || 0) - (a.ice_score || 0));

  return (
    <section className="space-y-6">
      <SectionHeader title="Product Recommendations" icon={Rocket} description="Actionable recommendations prioritized by ICE score" />

      {/* Quick Wins */}
      {content?.quick_wins && content.quick_wins.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-foreground">Quick Wins</h4>
          <div className="space-y-3">
            {content.quick_wins.map((rec, i) => (
              <RecommendationCard key={`qw-${i}`} rec={rec} accent="border-l-green-500" />
            ))}
          </div>
        </div>
      )}

      {/* Strategic Bets */}
      {content?.strategic_bets && content.strategic_bets.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-foreground">Strategic Bets</h4>
          <div className="space-y-3">
            {content.strategic_bets.map((rec, i) => (
              <RecommendationCard key={`sb-${i}`} rec={rec} accent="border-l-purple-500" />
            ))}
          </div>
        </div>
      )}

      {/* All Recommendations */}
      {(!content?.quick_wins && !content?.strategic_bets) && (
        <div className="space-y-3">
          {sorted.map((rec, i) => (
            <RecommendationCard key={i} rec={rec} />
          ))}
        </div>
      )}
    </section>
  );
}

function RecommendationCard({ rec, accent }: { rec: ProductRecommendation; accent?: string }) {
  const impact = Number(rec.impact_score) || 0;
  const effort = Number(rec.effort_score) || 0;
  const confidence = Number(rec.confidence_score) || 0;
  const rawIce = Number(rec.ice_score) || 0;
  const iceScore = rawIce > 0 ? rawIce : Math.round((impact * confidence) / Math.max(effort, 1));

  return (
    <div className={cn("rounded-lg border border-border bg-card p-5 space-y-4 border-l-4", accent || "border-l-primary")}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-foreground">{rec.title}</h4>
          <p className="text-sm text-muted-foreground mt-1">{rec.description}</p>
        </div>
        <span className="shrink-0 rounded-lg bg-primary/10 px-3 py-1 text-sm font-bold text-primary">
          ICE {iceScore}
        </span>
      </div>

      {rec.rationale && (
        <p className="text-xs text-muted-foreground">{rec.rationale}</p>
      )}

      {/* Score Bars */}
      <div className="space-y-2">
        <ProgressIndicator label="Impact" value={rec.impact_score} max={10} color="green" />
        <ProgressIndicator label="Effort" value={rec.effort_score} max={10} color="amber" />
        <ProgressIndicator label="Confidence" value={rec.confidence_score} max={10} color="default" />
      </div>

      {/* Footer */}
      <div className="flex flex-wrap items-center gap-3 pt-1">
        {rec.affected_personas && rec.affected_personas.length > 0 && (
          <span className="text-xs text-muted-foreground">
            Personas: {rec.affected_personas.join(", ")}
          </span>
        )}
        {rec.success_metric && (
          <span className="text-xs text-muted-foreground">
            Success: {rec.success_metric}
          </span>
        )}
      </div>
    </div>
  );
}
