// === Scrapers ===

export interface ScraperInfo {
  name: string;
  source: string;
  status: "ready" | "running" | "error";
  last_run: string | null;
  reviews_collected: number;
  runtime_seconds: number | null;
}

export interface ScraperStatus {
  run_id: number;
  status: "idle" | "running" | "completed" | "failed";
  sources: string[];
  progress_current: number;
  progress_total: number;
  current_source: string | null;
  current_message: string | null;
  reviews_collected: number;
}

// === Reviews ===

export interface Review {
  id: string;
  source: string;
  text_clean: string | null;
  title: string | null;
  author: string | null;
  rating: number | null;
  sentiment: string | null;
  date: string | null;
  url: string | null;
  quality_score: number | null;
}

export interface ReviewsResponse {
  reviews: Review[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// === Dashboard ===

export interface DashboardStats {
  total_reviews: number;
  reviews_today: number;
  sources_connected: number;
  total_sources: number;
  last_scrape: string | null;
  last_insight_run: string | null;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface SourceDistribution {
  source: string;
  count: number;
}

export interface SentimentDistribution {
  sentiment: string;
  count: number;
}

export interface Activity {
  type: "scrape" | "insight";
  message: string;
  status: string;
  timestamp: string;
}

// === Insights ===

export interface Insight {
  id: number;
  workflow: string;
  title: string | null;
  content: Record<string, unknown>;
  review_count: number | null;
  ai_model: string | null;
  created_at: string;
}

export interface InsightGenerationStatus {
  status: "idle" | "running" | "completed" | "failed";
  workflows_total: number;
  workflows_completed: number;
  current_workflow: string | null;
  current_step: string | null;
  errors: string[];
}

// === Reports ===

export interface Report {
  id: number;
  title: string;
  description: string | null;
  workflows: string[];
  sources: string[];
  review_count: number | null;
  status: string;
  created_at: string;
}

// === Settings ===

export interface AppSettings {
  gemini_api_key: string;
  grok_api_key: string;
  has_gemini_key: boolean;
  has_grok_key: boolean;
}

// === Workflow Definitions ===

export const AVAILABLE_WORKFLOWS = [
  { id: "executive_summary", name: "Executive Summary" },
  { id: "pain_points", name: "Pain Points" },
  { id: "feature_requests", name: "Feature Requests" },
  { id: "positive_feedback", name: "Positive Feedback" },
  { id: "negative_feedback", name: "Negative Feedback" },
  { id: "sentiment_analysis", name: "Sentiment Analysis" },
  { id: "competitor_mentions", name: "Competitor Mentions" },
  { id: "jobs_to_be_done", name: "Jobs To Be Done" },
  { id: "user_personas", name: "User Personas" },
  { id: "theme_clustering", name: "Theme Clustering" },
  { id: "emerging_trends", name: "Emerging Trends" },
  { id: "product_recommendations", name: "Product Recommendations" },
] as const;
