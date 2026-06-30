"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatDate, truncateText } from "@/lib/utils";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import type { ReviewsResponse } from "@/types";

export default function ReviewsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [sentiment, setSentiment] = useState("");
  const perPage = 25;

  const { data, isLoading } = useQuery<ReviewsResponse>({
    queryKey: ["reviews", page, search, source, sentiment],
    queryFn: () =>
      api
        .get("/reviews", {
          params: {
            page,
            per_page: perPage,
            ...(search && { search }),
            ...(source && { source }),
            ...(sentiment && { sentiment }),
          },
        })
        .then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Reviews</h2>

      {/* Search & Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search reviews..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-input bg-background px-10 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <select
          value={source}
          onChange={(e) => {
            setSource(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Sources</option>
          <option value="reddit">Reddit</option>
          <option value="app_store">App Store</option>
          <option value="play_store">Play Store</option>
          <option value="spotify_community">Spotify Community</option>
          <option value="social">Social Media</option>
        </select>
        <select
          value={sentiment}
          onChange={(e) => {
            setSentiment(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Sentiments</option>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Source</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Rating</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Date</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Review</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Sentiment</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={5} className="px-4 py-4">
                    <div className="h-4 bg-muted rounded animate-pulse" />
                  </td>
                </tr>
              ))
            ) : data?.reviews.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">
                  No reviews found. Try adjusting your filters or run a scraper.
                </td>
              </tr>
            ) : (
              data?.reviews.map((review) => (
                <tr key={review.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3">
                    <span className="inline-flex rounded-md bg-muted px-2 py-0.5 text-xs font-medium">
                      {review.source}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {review.rating ? `${"⭐".repeat(Math.round(review.rating))}` : "—"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDate(review.date)}
                  </td>
                  <td className="px-4 py-3 max-w-md">
                    <p className="text-foreground line-clamp-2">
                      {truncateText(review.text_clean || review.title || "—", 150)}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <SentimentBadge sentiment={review.sentiment} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, data.total)} of{" "}
            {data.total.toLocaleString()}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border border-input p-2 hover:bg-muted disabled:opacity-50 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm text-muted-foreground px-3">
              Page {page} of {data.total_pages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={page === data.total_pages}
              className="rounded-lg border border-input p-2 hover:bg-muted disabled:opacity-50 transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function SentimentBadge({ sentiment }: { sentiment: string | null }) {
  if (!sentiment) return <span className="text-muted-foreground">—</span>;

  const styles: Record<string, string> = {
    positive: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
    neutral: "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400",
    negative: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  };

  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${styles[sentiment] || ""}`}>
      {sentiment}
    </span>
  );
}
