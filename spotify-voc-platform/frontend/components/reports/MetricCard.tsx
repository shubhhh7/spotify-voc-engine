"use client";

import { type LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number | null;
  icon: LucideIcon;
}

function formatValue(value: string | number | null): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 10_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

export function MetricCard({ label, value, icon: Icon }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs text-muted-foreground font-medium">{label}</span>
      </div>
      <p className="text-2xl font-bold text-foreground">{formatValue(value)}</p>
    </div>
  );
}
