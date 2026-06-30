"use client";

import { formatRelativeTime, formatRuntime } from "@/lib/utils";
import { RefreshCw, CheckCircle2, XCircle } from "lucide-react";
import type { ScraperInfo } from "@/types";

interface ScraperCardProps {
  scraper: ScraperInfo;
  selected: boolean;
  onToggle: () => void;
}

export function ScraperCard({ scraper, selected, onToggle }: ScraperCardProps) {
  return (
    <div
      onClick={onToggle}
      className={`cursor-pointer rounded-lg border p-5 transition-all duration-200 ${
        selected
          ? "border-primary bg-primary/5 ring-1 ring-primary"
          : "border-border bg-card hover:border-muted-foreground/30"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-foreground">{scraper.name}</h3>
        <StatusBadge status={scraper.status} />
      </div>
      <div className="space-y-1.5 text-sm text-muted-foreground">
        <p>Last run: {formatRelativeTime(scraper.last_run)}</p>
        <p>Reviews: {scraper.reviews_collected.toLocaleString()}</p>
        <p>Runtime: {formatRuntime(scraper.runtime_seconds)}</p>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "running") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 dark:bg-blue-900/30 px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-300">
        <RefreshCw className="h-3 w-3 animate-spin" /> Running
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 dark:bg-red-900/30 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-300">
        <XCircle className="h-3 w-3" /> Error
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 dark:bg-green-900/30 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-300">
      <CheckCircle2 className="h-3 w-3" /> Ready
    </span>
  );
}
