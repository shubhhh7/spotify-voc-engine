"use client";

import { Users } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { EmptyState } from "./EmptyState";
import { cn } from "@/lib/utils";
import type { UserPersona } from "./types";

interface Props {
  content: { personas?: UserPersona[] } | null;
}

const CHURN_STYLES = {
  High: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  Medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  Low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

export function UserPersonasSection({ content }: Props) {
  const personas = content?.personas;

  if (!personas || personas.length === 0) {
    return <EmptyState icon={Users} title="No user personas generated" description="Generate persona analysis to understand distinct user segments." />;
  }

  return (
    <section className="space-y-6">
      <SectionHeader title="User Personas" icon={Users} description="Data-driven user segments from feedback analysis" />

      <div className="space-y-4">
        {personas.map((persona, i) => (
          <div key={i} className="rounded-lg border border-border bg-card p-6 space-y-4">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h4 className="text-base font-semibold text-foreground">{persona.name}</h4>
                <p className="text-sm text-muted-foreground mt-1">{persona.description}</p>
              </div>
              <div className="flex flex-col items-end gap-2 shrink-0">
                <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", CHURN_STYLES[persona.churn_risk])}>
                  {persona.churn_risk} churn risk
                </span>
                {persona.estimated_size && (
                  <span className="text-xs text-muted-foreground">{persona.estimated_size}</span>
                )}
              </div>
            </div>

            {/* Details Grid */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {persona.listening_behavior && (
                <div>
                  <span className="text-xs font-medium text-muted-foreground">Listening</span>
                  <p className="text-sm text-foreground mt-0.5">{persona.listening_behavior}</p>
                </div>
              )}
              <div>
                <span className="text-xs font-medium text-muted-foreground">Primary Need</span>
                <p className="text-sm text-foreground mt-0.5">{persona.primary_need}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-muted-foreground">Main Frustration</span>
                <p className="text-sm text-foreground mt-0.5">{persona.main_frustration}</p>
              </div>
              {persona.discovery_approach && (
                <div>
                  <span className="text-xs font-medium text-muted-foreground">Discovery</span>
                  <p className="text-sm text-foreground mt-0.5">{persona.discovery_approach}</p>
                </div>
              )}
            </div>

            {/* Quote */}
            {persona.representative_quote && (
              <blockquote className="border-l-2 border-primary/30 pl-4 text-sm italic text-muted-foreground">
                &ldquo;{persona.representative_quote}&rdquo;
              </blockquote>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
