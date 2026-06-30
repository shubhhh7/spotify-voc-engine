"use client";

import { RefreshCw } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import type { ScraperStatus } from "@/types";

interface ScraperProgressProps {
  status: ScraperStatus;
  logs: string[];
}

export function ScraperProgress({ status, logs }: ScraperProgressProps) {
  const progress =
    status.progress_total > 0
      ? (status.progress_current / status.progress_total) * 100
      : 0;

  return (
    <div className="rounded-lg border border-border bg-card p-6 space-y-4">
      <div className="flex items-center gap-2">
        <RefreshCw className="h-4 w-4 animate-spin text-primary" />
        <span className="font-medium text-sm">Running scrapers...</span>
        <span className="ml-auto text-sm text-muted-foreground">
          {status.reviews_collected} reviews collected
        </span>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>{status.current_message || status.current_source || ""}</span>
          <span>
            {status.progress_current}/{status.progress_total} sources
          </span>
        </div>
        <Progress value={progress} />
      </div>

      {/* Live Logs */}
      <div className="rounded-md bg-muted/50 p-4 max-h-48 overflow-y-auto font-mono text-xs">
        {logs.length > 0 ? (
          logs.map((line, i) => (
            <p key={i} className="text-muted-foreground leading-relaxed">
              {line}
            </p>
          ))
        ) : (
          <p className="text-muted-foreground">Starting...</p>
        )}
      </div>
    </div>
  );
}
