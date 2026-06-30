"use client";

import { Target } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { EmptyState } from "./EmptyState";
import { cn } from "@/lib/utils";
import type { JobToBeDone } from "./types";

interface Props {
  content: { jobs?: JobToBeDone[] } | null;
}

const SATISFACTION_STYLES = {
  Satisfied: "border-green-200 dark:border-green-900/50 bg-green-50/50 dark:bg-green-900/5",
  "Partially Satisfied": "border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-900/5",
  Unsatisfied: "border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-900/5",
};

const SATISFACTION_BADGE = {
  Satisfied: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  "Partially Satisfied": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  Unsatisfied: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export function JobsToBeDoneSection({ content }: Props) {
  const jobs = content?.jobs;

  if (!jobs || jobs.length === 0) {
    return <EmptyState icon={Target} title="No jobs-to-be-done identified" description="Generate JTBD analysis to understand user motivations." />;
  }

  return (
    <section className="space-y-6">
      <SectionHeader title="Jobs To Be Done" icon={Target} description="What users are hiring Spotify to do" />

      <div className="grid gap-4 md:grid-cols-2">
        {jobs.map((job, i) => {
          const isUnderserved = job.satisfaction === "Unsatisfied" || job.satisfaction === "Partially Satisfied";
          return (
            <div
              key={i}
              className={cn(
                "rounded-lg border p-5 space-y-3",
                isUnderserved
                  ? SATISFACTION_STYLES[job.satisfaction]
                  : "border-border bg-card"
              )}
            >
              {/* Job Statement */}
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">When</span> {job.situation}
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">I want to</span> {job.motivation}
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">So I can</span> {job.expected_outcome}
                </p>
              </div>

              {/* Satisfaction Badge */}
              <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", SATISFACTION_BADGE[job.satisfaction])}>
                {job.satisfaction}
              </span>

              {/* Barriers */}
              {job.barriers && job.barriers.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-muted-foreground">Barriers:</span>
                  <ul className="mt-1 space-y-0.5">
                    {job.barriers.slice(0, 10).map((b, j) => (
                      <li key={j} className="text-xs text-muted-foreground flex items-start gap-1">
                        <span className="text-red-400">•</span> {b}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Workarounds */}
              {job.workarounds && job.workarounds.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-muted-foreground">Workarounds:</span>
                  <ul className="mt-1 space-y-0.5">
                    {job.workarounds.slice(0, 10).map((w, j) => (
                      <li key={j} className="text-xs text-muted-foreground flex items-start gap-1">
                        <span className="text-amber-400">•</span> {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
