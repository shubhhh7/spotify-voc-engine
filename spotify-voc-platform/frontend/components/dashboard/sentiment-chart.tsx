"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { SentimentDistribution } from "@/types";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#1DB954",
  neutral: "#B3B3B3",
  negative: "#E85D75",
};

export function SentimentChart() {
  const { data, isLoading } = useQuery<SentimentDistribution[]>({
    queryKey: ["dashboard-sentiment"],
    queryFn: () => api.get("/dashboard/sentiment").then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        Loading sentiment data...
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        No sentiment data yet. Run AI analysis to classify reviews.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="sentiment" tick={{ fontSize: 12 }} className="text-muted-foreground" />
        <YAxis tick={{ fontSize: 11 }} className="text-muted-foreground" />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={SENTIMENT_COLORS[entry.sentiment] || "#B3B3B3"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
