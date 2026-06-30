"use client";

import { useState } from "react";
import { Star } from "lucide-react";
import { SourceBadge } from "./SourceBadge";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import type { RepresentativeReview } from "./types";

interface Props {
  review: RepresentativeReview;
}

export function ReviewCard({ review }: Props) {
  const [expanded, setExpanded] = useState(false);
  const shouldTruncate = review.text.length > 300;
  const displayText = shouldTruncate && !expanded ? review.text.slice(0, 300) + "…" : review.text;

  // Highlight keywords in text
  function renderText(text: string, keywords?: string[]) {
    if (!keywords || keywords.length === 0) return text;
    const regex = new RegExp(`(${keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
    const parts = text.split(regex);
    return parts.map((part, i) =>
      keywords.some(k => k.toLowerCase() === part.toLowerCase())
        ? <mark key={i} className="bg-yellow-200/60 dark:bg-yellow-900/40 px-0.5 rounded">{part}</mark>
        : part
    );
  }

  const sentimentColor =
    review.sentiment?.toLowerCase() === "positive" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
    review.sentiment?.toLowerCase() === "negative" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
    "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <SourceBadge source={review.source} />
          {review.sentiment && (
            <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", sentimentColor)}>
              {review.sentiment}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Stars */}
          {review.rating != null && (
            <div className="flex items-center gap-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={cn("h-3 w-3", i < review.rating ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30")}
                />
              ))}
            </div>
          )}
          {review.date && (
            <span className="text-xs text-muted-foreground">{formatDate(review.date)}</span>
          )}
        </div>
      </div>

      {/* Review Text */}
      <p className="text-sm text-foreground leading-relaxed">
        {renderText(displayText, review.keywords)}
      </p>

      {/* Expand toggle */}
      {shouldTruncate && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs font-medium text-primary hover:underline"
        >
          {expanded ? "Show less" : "Read more"}
        </button>
      )}
    </div>
  );
}
