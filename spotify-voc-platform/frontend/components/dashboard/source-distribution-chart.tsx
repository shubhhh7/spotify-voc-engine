"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { SourceDistribution } from "@/types";

const COLORS = ["#1DB954", "#4695F7", "#F5C542", "#E85D75", "#A78BFA", "#34D399"];

export function SourceDistributionChart() {
  const { data, isLoading } = useQuery<SourceDistribution[]>({
    queryKey: ["dashboard-sources"],
    queryFn: () => api.get("/dashboard/sources").then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        Loading source data...
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        No source data yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="source"
          cx="50%"
          cy="50%"
          outerRadius={70}
          label={({ source, percent }) =>
            `${source} (${(percent * 100).toFixed(0)}%)`
          }
          labelLine={false}
          fontSize={11}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
