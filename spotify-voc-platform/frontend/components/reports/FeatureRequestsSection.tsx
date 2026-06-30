"use client";

import { Lightbulb } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { PriorityBadge } from "./PriorityBadge";
import { EmptyState } from "./EmptyState";
import type { FeatureRequest } from "./types";

interface Props {
  content: { feature_requests?: FeatureRequest[] } | null;
}

function computePriority(req: FeatureRequest): "High" | "Medium" | "Low" {
  if (req.request_count >= 10 && req.business_value === "High") return "High";
  if (req.request_count < 5 || req.business_value === "Low") return "Low";
  return "Medium";
}

const PRIORITY_ORDER = { High: 0, Medium: 1, Low: 2 };

export function FeatureRequestsSection({ content }: Props) {
  const features = content?.feature_requests;

  if (!features || features.length === 0) {
    return <EmptyState icon={Lightbulb} title="No feature requests identified" description="Generate feature requests analysis to see what users want." />;
  }

  const sorted = [...features].sort((a, b) => {
    const pa = computePriority(a);
    const pb = computePriority(b);
    if (PRIORITY_ORDER[pa] !== PRIORITY_ORDER[pb]) return PRIORITY_ORDER[pa] - PRIORITY_ORDER[pb];
    return b.request_count - a.request_count;
  });

  return (
    <section className="space-y-6">
      <SectionHeader title="Feature Requests" icon={Lightbulb} description="Most requested features by demand and business value" />

      <div className="grid gap-4 md:grid-cols-2">
        {sorted.map((req, i) => {
          const priority = computePriority(req);
          return (
            <div key={i} className="rounded-lg border border-border bg-card p-5 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-sm font-semibold text-foreground">{req.title}</h4>
                <PriorityBadge priority={priority} />
              </div>

              <p className="text-sm text-muted-foreground">{req.description}</p>

              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  {req.request_count} requests
                </span>
                <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  Complexity: {req.complexity}
                </span>
                <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  Value: {req.business_value}
                </span>
              </div>

              {req.user_segments && req.user_segments.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {req.user_segments.map((seg, j) => (
                    <span key={j} className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                      {seg}
                    </span>
                  ))}
                </div>
              )}

              {req.representative_quote && (
                <blockquote className="border-l-2 border-primary/30 pl-3 text-xs italic text-muted-foreground">
                  &ldquo;{req.representative_quote}&rdquo;
                </blockquote>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
