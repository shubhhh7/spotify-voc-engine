// === Report Detail (full report with insights) ===

export interface ReportDetail {
  id: number;
  title: string;
  description: string | null;
  workflows: string[];
  sources: string[];
  review_count: number | null;
  date_range_start: string | null;
  date_range_end: string | null;
  status: string;
  created_at: string;
  report_count?: number;
  insights: InsightDetail[];
}

export interface InsightDetail {
  id: number;
  workflow: string;
  title: string | null;
  content: Record<string, unknown>;
  review_count: number | null;
  ai_model: string | null;
  created_at: string;
}

// === Executive Summary ===

export interface ExecutiveSummaryContent {
  bottom_line: string;
  key_findings: KeyFinding[];
  key_metric: string;
  overall_sentiment: string;
  confidence_score: number;
}

export interface KeyFinding {
  theme: string;
  severity: number;
  frequency: string;
  description: string;
}

// === Pain Points ===

export interface PainPoint {
  title: string;
  severity: number;
  frequency: number;
  category: string;
  explanation: string;
  representative_quotes: string[];
}

// === Feature Requests ===

export interface FeatureRequest {
  title: string;
  description: string;
  request_count: number;
  complexity: "Low" | "Medium" | "High";
  business_value: "Low" | "Medium" | "High";
  user_segments: string[];
  representative_quote: string;
}

// === Emerging Trends ===

export interface EmergingTrend {
  name: string;
  description: string;
  growth_signal: string;
  potential_impact: "High" | "Medium" | "Low";
  time_horizon: string;
  confidence: number;
}

// === Theme Clusters ===

export interface ThemeCluster {
  theme: string;
  review_count: number;
  sentiment_mix: string;
  key_insight: string;
  sub_themes: string[];
  representative_quotes: string[];
}

export interface ThemeClusteringContent {
  clusters: ThemeCluster[];
  cross_cutting_themes?: string[];
}

// === Jobs To Be Done ===

export interface JobToBeDone {
  situation: string;
  motivation: string;
  expected_outcome: string;
  satisfaction: "Satisfied" | "Partially Satisfied" | "Unsatisfied";
  barriers: string[];
  workarounds: string[];
}

// === Competitor Mentions ===

export interface CompetitorMention {
  competitor: string;
  mention_count: number;
  sentiment: "Positive" | "Neutral" | "Negative";
  context: string;
  perceived_advantage: string;
  representative_quotes: string[];
}

export interface CompetitorMentionsContent {
  competitors: CompetitorMention[];
  switching_signals?: SwitchingSignal[];
  spotify_advantages?: string[];
}

export interface SwitchingSignal {
  signal: string;
  target_competitor: string;
  reason: string;
}

// === User Personas ===

export interface UserPersona {
  name: string;
  description: string;
  listening_behavior?: string;
  primary_need: string;
  main_frustration: string;
  discovery_approach?: string;
  churn_risk: "High" | "Medium" | "Low";
  estimated_size: string;
  representative_quote?: string;
}

// === Product Recommendations ===

export interface ProductRecommendation {
  title: string;
  description: string;
  rationale: string;
  impact_score: number;
  effort_score: number;
  confidence_score: number;
  ice_score: number;
  affected_personas: string[];
  success_metric: string;
}

export interface ProductRecommendationsContent {
  recommendations: ProductRecommendation[];
  quick_wins?: ProductRecommendation[];
  strategic_bets?: ProductRecommendation[];
}

// === Sentiment Analysis ===

export interface SentimentAnalysisContent {
  overall_sentiment: {
    positive_pct: number;
    neutral_pct: number;
    negative_pct: number;
  };
  positive_drivers: string[];
  negative_drivers: string[];
  notable_shifts: string;
  by_topic?: Array<{
    topic: string;
    positive: number;
    neutral: number;
    negative: number;
  }>;
}

// === Representative Review ===

export interface RepresentativeReview {
  source: string;
  rating: number;
  date: string;
  sentiment: string;
  text: string;
  keywords?: string[];
  relevance_score?: number;
}
