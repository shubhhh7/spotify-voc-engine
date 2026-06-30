"use client";

import { Heart } from "lucide-react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { SectionHeader } from "./SectionHeader";
import { EmptyState } from "./EmptyState";
import type { SentimentAnalysisContent } from "./types";

interface Props {
  content: SentimentAnalysisContent | null;
}

const COLORS = { positive: "#1DB954", neutral: "#B3B3B3", negative: "#E85D75" };

export function SentimentSection({ content }: Props) {
  if (!content) {
    return <EmptyState icon={Heart} title="No sentiment analysis available" description="Generate sentiment analysis insights to visualize feedback emotions." />;
  }

  const pieData = content.overall_sentiment ? [
    { name: "Positive", value: Number(content.overall_sentiment.positive_pct) || 0, color: COLORS.positive },
    { name: "Neutral", value: Number(content.overall_sentiment.neutral_pct) || 0, color: COLORS.neutral },
    { name: "Negative", value: Number(content.overall_sentiment.negative_pct) || 0, color: COLORS.negative },
  ] : [];

  const topicData = (content.by_topic || [])
    .sort((a, b) => (b.positive + b.neutral + b.negative) - (a.positive + a.neutral + a.negative))
    .slice(0, 10);

  return (
    <section className="space-y-6">
      <SectionHeader title="Sentiment Analysis" icon={Heart} description="Emotional landscape of user feedback" />

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Pie Chart */}
        {pieData.length > 0 && pieData.some(d => d.value > 0) && (
          <div className="rounded-lg border border-border bg-card p-4">
            <h4 className="text-sm font-medium text-muted-foreground mb-3">Overall Sentiment</h4>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, value }) => `${name} ${value}%`} labelLine={false}>
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val: number) => `${val}%`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Bar Chart - By Topic */}
        {topicData.length > 0 && (
          <div className="rounded-lg border border-border bg-card p-4">
            <h4 className="text-sm font-medium text-muted-foreground mb-3">Sentiment by Topic</h4>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topicData} layout="vertical" margin={{ left: 80 }}>
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="topic" width={75} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="positive" stackId="a" fill={COLORS.positive} name="Positive" />
                  <Bar dataKey="neutral" stackId="a" fill={COLORS.neutral} name="Neutral" />
                  <Bar dataKey="negative" stackId="a" fill={COLORS.negative} name="Negative" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Driver Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {content.positive_drivers && content.positive_drivers.length > 0 && (
          <div className="rounded-lg border border-green-200 dark:border-green-900/50 bg-green-50/50 dark:bg-green-900/10 p-4">
            <h4 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Positive Drivers</h4>
            <ul className="space-y-1">
              {content.positive_drivers.map((d, i) => (
                <li key={i} className="text-sm text-foreground flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">+</span> {d}
                </li>
              ))}
            </ul>
          </div>
        )}

        {content.negative_drivers && content.negative_drivers.length > 0 && (
          <div className="rounded-lg border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-900/10 p-4">
            <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Negative Drivers</h4>
            <ul className="space-y-1">
              {content.negative_drivers.map((d, i) => (
                <li key={i} className="text-sm text-foreground flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">−</span> {d}
                </li>
              ))}
            </ul>
          </div>
        )}

        {content.notable_shifts && (
          <div className="rounded-lg border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-900/10 p-4">
            <h4 className="text-sm font-semibold text-amber-700 dark:text-amber-400 mb-2">Notable Shifts</h4>
            <p className="text-sm text-foreground">{content.notable_shifts}</p>
          </div>
        )}
      </div>
    </section>
  );
}
