"use client";

import { cn } from "@/lib/utils";
import type { JobToBeDone } from "../types";

interface Props {
  content: { jobs?: JobToBeDone[] } | null;
}

const SATISFACTION_BADGE = {
  Satisfied: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  "Partially Satisfied": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  Unsatisfied: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

export function JobsToBeDoneCompact({ content }: Props) {
  const jobs = content?.jobs;

  if (!jobs || jobs.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No jobs-to-be-done identified.</p>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {jobs.map((job, i) => (
        <div key={i} className="p-3 rounded-md border border-border space-y-2">
          {/* Job statement compact */}
          <div className="space-y-0.5">
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">When</span>{" "}
              <span className="line-clamp-1">{job.situation}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">I want</span>{" "}
              <span className="line-clamp-1">{job.motivation}</span>
            </p>
          </div>

          {/* Satisfaction + barriers */}
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-medium",
                SATISFACTION_BADGE[job.satisfaction]
              )}
            >
              {job.satisfaction}
            </span>
          </div>

          {/* Barrier details */}
          {job.barriers && job.barriers.length > 0 && (
            <div>
              <span className="text-[10px] font-medium text-muted-foreground">Barriers:</span>
              <ul className="mt-0.5 space-y-0.5">
                {job.barriers.slice(0, 3).map((b, j) => (
                  <li key={j} className="text-[10px] text-muted-foreground flex items-start gap-1">
                    <span className="text-red-400 shrink-0">•</span>
                    <span className="line-clamp-1">{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
