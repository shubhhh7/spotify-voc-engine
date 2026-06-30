/**
 * Data normalizers for AI-generated insight content.
 *
 * The LLM sometimes returns:
 * - Numbers as strings ("7.5" instead of 7.5)
 * - Different field names than what the frontend types expect
 * - Nested structures where flat ones are expected
 *
 * These normalizers bridge the gap between LLM output and our TypeScript types.
 */

import type {
  ProductRecommendationsContent,
  ProductRecommendation,
  SentimentAnalysisContent,
  JobToBeDone,
} from "./types";

/** Safely coerce a value to a number. Returns 0 if it can't be parsed. */
function toNum(val: unknown): number {
  if (typeof val === "number" && !isNaN(val)) return val;
  if (typeof val === "string") {
    const parsed = parseFloat(val);
    return isNaN(parsed) ? 0 : parsed;
  }
  return 0;
}

// ─── Product Recommendations ────────────────────────────────────────────────

function normalizeRecommendation(raw: Record<string, unknown>): ProductRecommendation {
  const impact = toNum(raw.impact_score);
  const effort = toNum(raw.effort_score);
  const confidence = toNum(raw.confidence_score);
  const iceRaw = toNum(raw.ice_score);
  const iceComputed = Math.round((impact * confidence) / Math.max(effort, 1));

  return {
    title: String(raw.title || ""),
    description: String(raw.description || ""),
    rationale: String(raw.rationale || ""),
    impact_score: impact,
    effort_score: effort,
    confidence_score: confidence,
    ice_score: iceRaw > 0 ? iceRaw : iceComputed,
    affected_personas: Array.isArray(raw.affected_personas) ? raw.affected_personas : [],
    success_metric: String(raw.success_metric || ""),
  };
}

export function normalizeProductRecommendations(
  content: Record<string, unknown> | null | undefined
): ProductRecommendationsContent | null {
  if (!content) return null;

  const recs = Array.isArray(content.recommendations)
    ? content.recommendations.map((r: Record<string, unknown>) => normalizeRecommendation(r))
    : [];

  const quickWins = Array.isArray(content.quick_wins)
    ? content.quick_wins.map((r: Record<string, unknown>) =>
        typeof r === "string" ? null : normalizeRecommendation(r)
      ).filter(Boolean) as ProductRecommendation[]
    : [];

  const strategicBets = Array.isArray(content.strategic_bets)
    ? content.strategic_bets.map((r: Record<string, unknown>) =>
        typeof r === "string" ? null : normalizeRecommendation(r)
      ).filter(Boolean) as ProductRecommendation[]
    : [];

  return { recommendations: recs, quick_wins: quickWins, strategic_bets: strategicBets };
}

// ─── Sentiment Analysis ─────────────────────────────────────────────────────

export function normalizeSentiment(
  content: Record<string, unknown> | null | undefined
): SentimentAnalysisContent | null {
  if (!content) return null;

  // overall_sentiment may have string percents
  const os = content.overall_sentiment as Record<string, unknown> | undefined;
  const overallSentiment = os
    ? {
        positive_pct: toNum(os.positive_pct),
        neutral_pct: toNum(os.neutral_pct),
        negative_pct: toNum(os.negative_pct),
      }
    : { positive_pct: 0, neutral_pct: 0, negative_pct: 0 };

  // Drivers may be nested under "sentiment_drivers" or at top level
  const drivers = (content.sentiment_drivers as Record<string, unknown>) || {};
  const posDrivers = (
    (content.positive_drivers as string[]) ||
    (drivers.positive_drivers as string[]) ||
    []
  );
  const negDrivers = (
    (content.negative_drivers as string[]) ||
    (drivers.negative_drivers as string[]) ||
    []
  );

  const notableShifts = String(content.notable_shifts || "");

  // by_topic: coerce numbers
  const byTopic = Array.isArray(content.by_topic)
    ? content.by_topic.map((t: Record<string, unknown>) => ({
        topic: String(t.topic || ""),
        positive: toNum(t.positive),
        neutral: toNum(t.neutral),
        negative: toNum(t.negative),
      }))
    : undefined;

  return {
    overall_sentiment: overallSentiment,
    positive_drivers: posDrivers,
    negative_drivers: negDrivers,
    notable_shifts: notableShifts,
    by_topic: byTopic,
  };
}

// ─── Jobs To Be Done ────────────────────────────────────────────────────────

function parseJobStatement(stmt: string): { situation: string; motivation: string; expected_outcome: string } {
  // Expected format: "When I [situation], I want to [motivation], so I can [outcome]"
  const whenMatch = stmt.match(/[Ww]hen\s+I\s+(.+?),\s*I\s+want\s+to\s+(.+?),\s*so\s+I\s+can\s+(.+)/i);
  if (whenMatch) {
    return {
      situation: whenMatch[1].trim(),
      motivation: whenMatch[2].trim(),
      expected_outcome: whenMatch[3].trim(),
    };
  }
  // Fallback: just use the whole statement as situation
  return { situation: stmt, motivation: "", expected_outcome: "" };
}

function normalizeJob(raw: Record<string, unknown>): JobToBeDone {
  // The LLM returns "job_statement" as a single string; frontend expects separate fields
  let situation = raw.situation as string | undefined;
  let motivation = raw.motivation as string | undefined;
  let expectedOutcome = raw.expected_outcome as string | undefined;

  if (!situation && raw.job_statement) {
    const parsed = parseJobStatement(String(raw.job_statement));
    situation = parsed.situation;
    motivation = parsed.motivation;
    expectedOutcome = parsed.expected_outcome;
  }

  // LLM returns "current_satisfaction"; frontend expects "satisfaction"
  const satisfaction = (raw.satisfaction || raw.current_satisfaction || "Partially Satisfied") as
    | "Satisfied"
    | "Partially Satisfied"
    | "Unsatisfied";

  return {
    situation: situation || "",
    motivation: motivation || "",
    expected_outcome: expectedOutcome || "",
    satisfaction,
    barriers: Array.isArray(raw.barriers) ? raw.barriers.map(String) : [],
    workarounds: Array.isArray(raw.workarounds) ? raw.workarounds.map(String) : [],
  };
}

export function normalizeJobsToBeDone(
  content: Record<string, unknown> | null | undefined
): { jobs: JobToBeDone[] } | null {
  if (!content) return null;

  const rawJobs = Array.isArray(content.jobs) ? content.jobs : [];
  const jobs = rawJobs.map((j: Record<string, unknown>) => normalizeJob(j));

  return { jobs };
}
