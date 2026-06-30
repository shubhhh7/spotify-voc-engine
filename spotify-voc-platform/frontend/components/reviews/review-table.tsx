"use client";

import { formatDate, truncateText } from "@/lib/utils";
import type { Review } from "@/types";

interface ReviewTableProps {
  reviews: Review[];
  isLoading: boolean;
}

export function ReviewTable({ reviews, isLoading }: ReviewTableProps) {
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          <tr>
            <th className="text-left px-4 py-3 font-medium text-muted-foreground">
              Source
            </th>
            <th className="text-left px-4 py-3 font-medium text-muted-foreground">
              Rating
            </th>
            <th className="text-left px-4 py-3 font-medium text-muted-foreground">
              Date
            </th>
            <th className="text-left px-4 py-3 font-medium text-muted-foreground">
              Review
            </th>
            <th className="text-left px-4 py-3 font-medium text-muted-foreground">
              Sentiment
            </th>
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
          ) : reviews.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="px-4 py-12 text-center text-muted-foreground"
              >
                No reviews found. Try adjusting your filters or run a scraper.
              </td>
            </tr>
          ) : (
            reviews.map((review) => (
              <tr
                key={review.id}
                className="hover:bg-muted/30 transition-colors"
              >
                <td className="px-4 py-3">
                  <span className="inline-flex rounded-md bg-muted px-2 py-0.5 text-xs font-medium">
                    {review.source}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {review.rating
                    ? `${"⭐".repeat(Math.min(Math.round(review.rating), 5))}`
                    : "—"}
                </td>
                <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                  {formatDate(review.date)}
                </td>
                <td className="px-4 py-3 max-w-md">
                  <p className="text-foreground line-clamp-2">
                    {truncateText(
                      review.text_clean || review.title || "—",
                      150
                    )}
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
  );
}

function SentimentBadge({ sentiment }: { sentiment: string | null }) {
  if (!sentiment) return <span className="text-muted-foreground">—</span>;

  const styles: Record<string, string> = {
    positive:
      "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
    neutral: "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400",
    negative:
      "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        styles[sentiment] || ""
      }`}
    >
      {sentiment}
    </span>
  );
}
