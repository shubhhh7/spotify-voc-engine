"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import type { SentimentAnalysisContent } from "../types";

interface Props {
  content: SentimentAnalysisContent | null;
}

const COLORS = { positive: "#1DB954", neutral: "#B3B3B3", negative: "#E85D75" };

export function SentimentCompact({ content }: Props) {
  if (!content) {
    return (
      <p className="text-sm text-muted-foreground">No sentiment data available.</p>
    );
  }

  const pieData = content.overall_sentiment
    ? [
        { name: "Positive", value: Number(content.overall_sentiment.positive_pct) || 0, color: COLORS.positive },
        { name: "Neutral", value: Number(content.overall_sentiment.neutral_pct) || 0, color: COLORS.neutral },
        { name: "Negative", value: Number(content.overall_sentiment.negative_pct) || 0, color: COLORS.negative },
      ]
    : [];

  return (
    <div className="flex gap-4 h-full">
      {/* Left: Pie Chart */}
      {pieData.length > 0 && pieData.some(d => d.value > 0) && (
        <div className="w-[140px] shrink-0">
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={35}
                outerRadius={60}
                dataKey="value"
                strokeWidth={2}
              >
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(val: number) => `${val}%`} />
            </PieChart>
          </ResponsiveContainer>
          {/* Legend below chart */}
          <div className="flex flex-col gap-1 mt-1">
            {pieData.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5 text-xs">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: d.color }}
                />
                <span className="text-muted-foreground">{d.name}</span>
                <span className="font-medium text-foreground ml-auto">{d.value}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Right: Drivers summary */}
      <div className="flex-1 space-y-3 min-w-0">
        {content.positive_drivers && content.positive_drivers.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-green-600 dark:text-green-400 mb-1">
              Positive Drivers
            </h4>
            <ul className="space-y-0.5">
              {content.positive_drivers.slice(0, 3).map((d, i) => (
                <li key={i} className="text-xs text-foreground flex items-start gap-1.5">
                  <span className="text-green-500 mt-0.5 shrink-0">+</span>
                  <span className="line-clamp-1">{d}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {content.negative_drivers && content.negative_drivers.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-red-600 dark:text-red-400 mb-1">
              Negative Drivers
            </h4>
            <ul className="space-y-0.5">
              {content.negative_drivers.slice(0, 3).map((d, i) => (
                <li key={i} className="text-xs text-foreground flex items-start gap-1.5">
                  <span className="text-red-500 mt-0.5 shrink-0">−</span>
                  <span className="line-clamp-1">{d}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {content.notable_shifts && (
          <div>
            <h4 className="text-xs font-semibold text-amber-600 dark:text-amber-400 mb-1">
              Notable Shift
            </h4>
            <p className="text-xs text-muted-foreground line-clamp-2">
              {content.notable_shifts}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
