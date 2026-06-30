"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { MessageSquare, TrendingUp, Plug, Clock } from "lucide-react";
import { StatCard } from "@/components/dashboard/stat-card";
import { ReviewTrendChart } from "@/components/dashboard/review-trend-chart";
import { SourceDistributionChart } from "@/components/dashboard/source-distribution-chart";
import { SentimentChart } from "@/components/dashboard/sentiment-chart";
import type { DashboardStats, Activity } from "@/types";

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.get("/dashboard/stats").then((r) => r.data),
  });

  const { data: activity } = useQuery<Activity[]>({
    queryKey: ["dashboard-activity"],
    queryFn: () => api.get("/dashboard/activity").then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Dashboard</h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Reviews"
          value={statsLoading ? "—" : (stats?.total_reviews ?? 0).toLocaleString()}
          icon={<MessageSquare className="h-5 w-5" />}
        />
        <StatCard
          title="Reviews Today"
          value={statsLoading ? "—" : (stats?.reviews_today ?? 0)}
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <StatCard
          title="Sources Connected"
          value={
            statsLoading
              ? "—"
              : `${stats?.sources_connected ?? 0}/${stats?.total_sources ?? 5}`
          }
          icon={<Plug className="h-5 w-5" />}
        />
        <StatCard
          title="Last Scrape"
          value={statsLoading ? "—" : formatRelativeTime(stats?.last_scrape ?? null)}
          icon={<Clock className="h-5 w-5" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">
            Review Trend (Last 30 Days)
          </h3>
          <ReviewTrendChart />
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">
            Source Distribution
          </h3>
          <SourceDistributionChart />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">
            Sentiment Distribution
          </h3>
          <SentimentChart />
        </div>

        {/* Recent Activity */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">
            Recent Activity
          </h3>
          {activity && activity.length > 0 ? (
            <div className="space-y-3 max-h-[200px] overflow-y-auto">
              {activity.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        item.status === "completed"
                          ? "bg-green-500"
                          : item.status === "failed"
                          ? "bg-red-500"
                          : "bg-yellow-500"
                      }`}
                    />
                    <span className="text-foreground">{item.message}</span>
                  </div>
                  <span className="text-muted-foreground text-xs whitespace-nowrap ml-2">
                    {formatRelativeTime(item.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No activity yet. Run a scraper to get started.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
