"use client";

import { useState, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  ReportHeader,
  KeyMetricsRow,
  SkeletonReport,
  EmptyState,
} from "@/components/reports";
import { DashboardCard } from "@/components/reports/DashboardCard";
import { ExecutiveSummaryCompact } from "@/components/reports/dashboard/ExecutiveSummaryCompact";
import { SentimentCompact } from "@/components/reports/dashboard/SentimentCompact";
import { PainPointsCompact } from "@/components/reports/dashboard/PainPointsCompact";
import { FeatureRequestsCompact } from "@/components/reports/dashboard/FeatureRequestsCompact";
import { EmergingTrendsCompact } from "@/components/reports/dashboard/EmergingTrendsCompact";
import { ThemeClustersCompact } from "@/components/reports/dashboard/ThemeClustersCompact";
import { CompetitorMentionsCompact } from "@/components/reports/dashboard/CompetitorMentionsCompact";
import { ProductRecommendationsCompact } from "@/components/reports/dashboard/ProductRecommendationsCompact";
import { UserPersonasCompact } from "@/components/reports/dashboard/UserPersonasCompact";
import { JobsToBeDoneCompact } from "@/components/reports/dashboard/JobsToBeDoneCompact";
import {
  FileText,
  Heart,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  Layers,
  Swords,
  Rocket,
  Users,
  Target,
} from "lucide-react";
import type { ReportDetail } from "@/components/reports/types";
import type {
  SentimentAnalysisContent,
  PainPoint,
  FeatureRequest,
  EmergingTrend,
  ThemeClusteringContent,
  CompetitorMentionsContent,
  ProductRecommendationsContent,
  UserPersona,
  JobToBeDone,
  ExecutiveSummaryContent,
} from "@/components/reports/types";
import {
  normalizeProductRecommendations,
  normalizeSentiment,
  normalizeJobsToBeDone,
} from "@/components/reports/normalizers";

// Toast state
type ToastType = "success" | "info" | "error";

export default function ReportsPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);
  const toastTimeout = useRef<NodeJS.Timeout | null>(null);

  const { data: report, isLoading, isError, refetch } = useQuery<ReportDetail | null>({
    queryKey: ["cumulative-report"],
    queryFn: async () => {
      // Fetch cumulative report that aggregates ALL past reports
      const cumulativeRes = await api.get("/reports/cumulative/all");
      const data = cumulativeRes.data;
      if (!data) return null;
      return data as ReportDetail;
    },
  });

  function showToast(message: string, type: ToastType) {
    if (toastTimeout.current) clearTimeout(toastTimeout.current);
    setToast({ message, type });
    toastTimeout.current = setTimeout(() => setToast(null), 4000);
  }

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refetch();
      showToast("Report updated", "success");
    } catch {
      showToast("Unable to fetch latest report", "error");
    } finally {
      setIsRefreshing(false);
    }
  }, [refetch]);

  function handleExport() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report_${report.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading) {
    return (
      <div className="w-full">
        <SkeletonReport />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="w-full">
        <EmptyState
          icon={FileText}
          title="Failed to load report"
          description="Could not retrieve the latest report. Please check your connection and try again."
        />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="w-full">
        <div className="rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center">
          <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No reports yet</h3>
          <p className="text-sm text-muted-foreground">
            Generate insights and save them as a report to see your analytics dashboard here.
          </p>
        </div>
      </div>
    );
  }

  // Extract insight data
  const getInsight = (workflow: string) =>
    report.insights?.find((i) => i.workflow === workflow);

  const execSummary = getInsight("executive_summary")?.content as ExecutiveSummaryContent | undefined;
  const sentiment = normalizeSentiment(getInsight("sentiment_analysis")?.content as Record<string, unknown> | undefined);
  const painPoints = getInsight("pain_points")?.content as { pain_points?: PainPoint[] } | undefined;
  const featureRequests = getInsight("feature_requests")?.content as { feature_requests?: FeatureRequest[] } | undefined;
  const emergingTrends = getInsight("emerging_trends")?.content as { trends?: EmergingTrend[] } | undefined;
  const themeClusters = getInsight("theme_clustering")?.content as ThemeClusteringContent | undefined;
  const competitors = getInsight("competitor_mentions")?.content as CompetitorMentionsContent | undefined;
  const recommendations = normalizeProductRecommendations(getInsight("product_recommendations")?.content as Record<string, unknown> | undefined);
  const personas = getInsight("user_personas")?.content as { personas?: UserPersona[] } | undefined;
  const jobs = normalizeJobsToBeDone(getInsight("jobs_to_be_done")?.content as Record<string, unknown> | undefined);

  return (
    <div className="w-full space-y-4 relative">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-20 right-6 z-50 rounded-lg px-4 py-3 text-sm font-medium shadow-lg transition-all animate-in slide-in-from-top-2 ${
            toast.type === "success"
              ? "bg-green-600 text-white"
              : toast.type === "error"
              ? "bg-red-600 text-white"
              : "bg-foreground text-background"
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Report Header — compact */}
      <ReportHeader
        report={report}
        onExport={handleExport}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Metrics Row */}
      <KeyMetricsRow report={report} />

      {/* Dashboard Grid — Row 1: Executive Summary + Sentiment */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DashboardCard
          title="Executive Summary"
          icon={<FileText className="h-4 w-4 text-primary" />}
          height="h-[340px]"
        >
          <ExecutiveSummaryCompact content={execSummary ?? null} />
        </DashboardCard>

        <DashboardCard
          title="Sentiment Analysis"
          icon={<Heart className="h-4 w-4 text-primary" />}
          height="h-[340px]"
        >
          <SentimentCompact content={sentiment ?? null} />
        </DashboardCard>
      </div>

      {/* Dashboard Grid — Row 2: Pain Points + Feature Requests */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DashboardCard
          title="Pain Points"
          icon={<AlertTriangle className="h-4 w-4 text-primary" />}
          height="h-[380px]"
        >
          <PainPointsCompact content={painPoints ?? null} />
        </DashboardCard>

        <DashboardCard
          title="Feature Requests"
          icon={<Lightbulb className="h-4 w-4 text-primary" />}
          height="h-[380px]"
        >
          <FeatureRequestsCompact content={featureRequests ?? null} />
        </DashboardCard>
      </div>

      {/* Dashboard Grid — Row 3: Emerging Trends + Theme Clusters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DashboardCard
          title="Emerging Trends"
          icon={<TrendingUp className="h-4 w-4 text-primary" />}
          height="h-[340px]"
        >
          <EmergingTrendsCompact content={emergingTrends ?? null} />
        </DashboardCard>

        <DashboardCard
          title="Theme Clusters"
          icon={<Layers className="h-4 w-4 text-primary" />}
          height="h-[340px]"
        >
          <ThemeClustersCompact content={themeClusters ?? null} />
        </DashboardCard>
      </div>

      {/* Dashboard Grid — Row 4: Recommendations (full width) */}
      <DashboardCard
        title="Product Recommendations"
        icon={<Rocket className="h-4 w-4 text-primary" />}
        height="h-[360px]"
        fullWidth
      >
        <ProductRecommendationsCompact content={recommendations ?? null} />
      </DashboardCard>

      {/* Dashboard Grid — Row 5: Competitors + User Personas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DashboardCard
          title="Competitor Mentions"
          icon={<Swords className="h-4 w-4 text-primary" />}
          height="h-[320px]"
        >
          <CompetitorMentionsCompact content={competitors ?? null} />
        </DashboardCard>

        <DashboardCard
          title="User Personas"
          icon={<Users className="h-4 w-4 text-primary" />}
          height="h-[320px]"
        >
          <UserPersonasCompact content={personas ?? null} />
        </DashboardCard>
      </div>

      {/* Dashboard Grid — Row 6: Jobs To Be Done (full width) */}
      <DashboardCard
        title="Jobs To Be Done"
        icon={<Target className="h-4 w-4 text-primary" />}
        height="h-[300px]"
        fullWidth
      >
        <JobsToBeDoneCompact content={jobs ?? null} />
      </DashboardCard>
    </div>
  );
}
