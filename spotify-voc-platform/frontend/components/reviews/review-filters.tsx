"use client";

import { Search } from "lucide-react";

interface ReviewFiltersProps {
  search: string;
  source: string;
  sentiment: string;
  onSearchChange: (value: string) => void;
  onSourceChange: (value: string) => void;
  onSentimentChange: (value: string) => void;
}

export function ReviewFilters({
  search,
  source,
  sentiment,
  onSearchChange,
  onSourceChange,
  onSentimentChange,
}: ReviewFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <div className="relative flex-1 min-w-[240px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search reviews..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full rounded-lg border border-input bg-background px-10 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <select
        value={source}
        onChange={(e) => onSourceChange(e.target.value)}
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
        onChange={(e) => onSentimentChange(e.target.value)}
        className="rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <option value="">All Sentiments</option>
        <option value="positive">Positive</option>
        <option value="neutral">Neutral</option>
        <option value="negative">Negative</option>
      </select>
    </div>
  );
}
