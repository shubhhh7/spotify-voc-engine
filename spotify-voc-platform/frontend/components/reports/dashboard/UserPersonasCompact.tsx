"use client";

import { cn } from "@/lib/utils";
import type { UserPersona } from "../types";

interface Props {
  content: { personas?: UserPersona[] } | null;
}

const CHURN_STYLES = {
  High: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  Medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  Low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

export function UserPersonasCompact({ content }: Props) {
  const personas = content?.personas;

  if (!personas || personas.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No personas generated.</p>
    );
  }

  return (
    <div className="space-y-2">
      {personas.map((persona, i) => (
        <div
          key={i}
          className="p-2.5 rounded-md border border-border"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-medium text-foreground truncate">
              {persona.name}
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-medium shrink-0",
                CHURN_STYLES[persona.churn_risk]
              )}
            >
              {persona.churn_risk} churn
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <span className="truncate">Need: {persona.primary_need}</span>
          </div>
          <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
            <span className="truncate">Frustration: {persona.main_frustration}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
