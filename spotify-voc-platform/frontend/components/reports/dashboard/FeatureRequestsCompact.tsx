"use client";

import { PriorityBadge } from "../PriorityBadge";
import type { FeatureRequest } from "../types";

interface Props {
  content: { feature_requests?: FeatureRequest[] } | null;
}

function computePriority(req: FeatureRequest): "High" | "Medium" | "Low" {
  if (req.request_count >= 10 && req.business_value === "High") return "High";
  if (req.request_count < 5 || req.business_value === "Low") return "Low";
  return "Medium";
}

const PRIORITY_ORDER = { High: 0, Medium: 1, Low: 2 };

export function FeatureRequestsCompact({ content }: Props) {
  const features = content?.feature_requests;

  if (!features || features.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No feature requests identified.</p>
    );
  }

  const sorted = [...features].sort((a, b) => {
    const pa = computePriority(a);
    const pb = computePriority(b);
    if (PRIORITY_ORDER[pa] !== PRIORITY_ORDER[pb]) return PRIORITY_ORDER[pa] - PRIORITY_ORDER[pb];
    return b.request_count - a.request_count;
  });

  return (
    <div className="space-y-2">
      {sorted.map((req, i) => {
        const priority = computePriority(req);
        return (
          <div
            key={i}
            className="flex items-start gap-3 p-2 rounded-md hover:bg-muted/50 transition-colors"
          >
            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-foreground truncate">
                  {req.title}
                </span>
                <PriorityBadge priority={priority} />
              </div>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                <span className="text-xs text-muted-foreground">
                  {req.request_count} requests
                </span>
                <span className="text-xs text-muted-foreground">
                  • Complexity: {req.complexity}
                </span>
                <span className="text-xs text-muted-foreground">
                  • Value: {req.business_value}
                </span>
              </div>
            </div>

            {/* User segments as chips */}
            {req.user_segments && req.user_segments.length > 0 && (
              <div className="hidden xl:flex flex-wrap gap-1 shrink-0 max-w-[120px]">
                {req.user_segments.slice(0, 2).map((seg, j) => (
                  <span
                    key={j}
                    className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary"
                  >
                    {seg}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
