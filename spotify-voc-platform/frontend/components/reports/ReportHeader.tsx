"use client";

import { Download, RefreshCw, Calendar, Hash, Cpu } from "lucide-react";
import { SourceBadge } from "./SourceBadge";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { ReportDetail } from "./types";

interface Props {
  report: ReportDetail;
  onExport: () => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export function ReportHeader({ report, onExport, onRefresh, isRefreshing }: Props) {
  const aiModel = report.insights?.[0]?.ai_model;

  return (
    <div className="space-y-4">
      {/* Title row */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-foreground">{report.title}</h1>
          {report.description && (
            <p className="text-sm text-muted-foreground">{report.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={onExport}
            className="inline-flex items-center gap-2 rounded-lg border border-input px-3 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            {isRefreshing ? "Refreshing…" : "Refresh Report"}
          </button>
        </div>
      </div>

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5" />
          {formatDate(report.created_at)}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Hash className="h-3.5 w-3.5" />
          {report.review_count?.toLocaleString() || 0} reviews
        </span>
        {aiModel && (
          <span className="inline-flex items-center gap-1.5">
            <Cpu className="h-3.5 w-3.5" />
            {aiModel}
          </span>
        )}
      </div>

      {/* Source badges */}
      {report.sources && report.sources.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {report.sources.map((source) => (
            <SourceBadge key={source} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}
