"use client";

import {
  MessageSquare,
  Star,
  ThumbsUp,
  ThumbsDown,
  Minus,
  Layers,
  Lightbulb,
  Bug,
} from "lucide-react";
import { MetricCard } from "./MetricCard";
import type { ReportDetail } from "./types";
import type { SentimentAnalysisContent } from "./types";

interface Props {
  report: ReportDetail;
}

export function KeyMetricsRow({ report }: Props) {
  // Extract metrics from insights
  const sentimentInsight = report.insights?.find(i => i.workflow === "sentiment_analysis");
  const themeInsight = report.insights?.find(i => i.workflow === "theme_clustering");
  const featureInsight = report.insights?.find(i => i.workflow === "feature_requests");
  const painPointInsight = report.insights?.find(i => i.workflow === "pain_points");

  const sentiment = sentimentInsight?.content as SentimentAnalysisContent | undefined;
  const positivePct = sentiment?.overall_sentiment?.positive_pct ?? null;
  const negativePct = sentiment?.overall_sentiment?.negative_pct ?? null;
  const neutralPct = sentiment?.overall_sentiment?.neutral_pct ?? null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const topicCount = (themeInsight?.content as any)?.clusters?.length ?? null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const featureCount = (featureInsight?.content as any)?.feature_requests?.length ?? null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const bugCount = (painPointInsight?.content as any)?.pain_points?.filter((p: any) => p.category?.toLowerCase().includes("bug"))?.length ?? null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
      <MetricCard label="Total Reviews" value={report.review_count} icon={MessageSquare} />
      <MetricCard label="Avg Rating" value={null} icon={Star} />
      <MetricCard label="Positive" value={positivePct != null ? `${Math.round(positivePct)}%` : null} icon={ThumbsUp} />
      <MetricCard label="Negative" value={negativePct != null ? `${Math.round(negativePct)}%` : null} icon={ThumbsDown} />
      <MetricCard label="Neutral" value={neutralPct != null ? `${Math.round(neutralPct)}%` : null} icon={Minus} />
      <MetricCard label="Topics" value={topicCount} icon={Layers} />
      <MetricCard label="Features" value={featureCount} icon={Lightbulb} />
      <MetricCard label="Bugs" value={bugCount} icon={Bug} />
    </div>
  );
}
