"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatRelativeTime, formatRuntime } from "@/lib/utils";
import { RefreshCw, Play, CheckCircle2, XCircle } from "lucide-react";
import type { ScraperInfo, ScraperStatus } from "@/types";

export default function ScrapersPage() {
  const [selected, setSelected] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const prevIsRunning = useRef(false);
  const queryClient = useQueryClient();

  const { data: scrapers } = useQuery<ScraperInfo[]>({
    queryKey: ["scrapers"],
    queryFn: () => api.get("/scrapers").then((r) => r.data),
  });

  const { data: status } = useQuery<ScraperStatus>({
    queryKey: ["scraper-status"],
    queryFn: () => api.get("/scrapers/status").then((r) => r.data),
    refetchInterval: isRunning ? 2000 : 10000,
  });

  const { data: logs } = useQuery<{ logs: string[] }>({
    queryKey: ["scraper-logs"],
    queryFn: () => api.get("/scrapers/logs").then((r) => r.data),
    refetchInterval: isRunning ? 2000 : false,
  });

  // Sync isRunning with actual backend status
  useEffect(() => {
    if (status?.status === "running" && !isRunning) {
      setIsRunning(true);
    } else if (status?.status !== "running" && status?.status !== undefined && isRunning) {
      setIsRunning(false);
    }
  }, [status?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  // Refetch scrapers list when a run finishes
  useEffect(() => {
    if (prevIsRunning.current && !isRunning) {
      queryClient.invalidateQueries({ queryKey: ["scrapers"] });
    }
    prevIsRunning.current = isRunning;
  }, [isRunning, queryClient]);

  const runMutation = useMutation({
    mutationFn: (sources: string[]) =>
      api.post("/scrapers/run", { sources }),
    onSuccess: () => {
      setIsRunning(true);
    },
  });

  const toggleSource = (source: string) => {
    setSelected((prev) =>
      prev.includes(source)
        ? prev.filter((s) => s !== source)
        : [...prev, source]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Scrapers</h2>
        <button
          onClick={() => runMutation.mutate(selected)}
          disabled={selected.length === 0 || isRunning}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Play className="h-4 w-4" />
          Run Selected ({selected.length})
        </button>
      </div>

      {/* Scraper Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {scrapers?.map((scraper) => (
          <div
            key={scraper.source}
            onClick={() => toggleSource(scraper.source)}
            className={`cursor-pointer rounded-lg border p-5 transition-all duration-200 ${
              selected.includes(scraper.source)
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
        ))}
      </div>

      {/* Progress Panel */}
      {isRunning && (
        <div className="rounded-lg border border-border bg-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin text-primary" />
            <span className="font-medium">Running...</span>
          </div>

          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{status?.current_message}</span>
              <span>
                {status?.progress_current}/{status?.progress_total} sources
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted">
              <div
                className="h-2 rounded-full bg-primary transition-all duration-500"
                style={{
                  width: `${
                    status?.progress_total
                      ? (status.progress_current / status.progress_total) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>

          {/* Live Logs */}
          <div className="rounded-md bg-muted/50 p-4 max-h-48 overflow-y-auto font-mono text-xs">
            {logs?.logs.map((line, i) => (
              <p key={i} className="text-muted-foreground">
                {line}
              </p>
            ))}
          </div>
        </div>
      )}
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
