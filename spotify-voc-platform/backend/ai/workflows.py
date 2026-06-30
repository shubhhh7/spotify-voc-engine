"""
Workflow definitions for AI insight generation.
Each workflow has a name, description, and prompt template.
"""

WORKFLOWS = {
    "executive_summary": {
        "name": "Executive Summary",
        "description": "High-level overview of all feedback themes and key takeaways",
        "prompt_template": """You are a senior Product Insights analyst at Spotify. Analyze the following user feedback and produce an executive summary.

INSTRUCTIONS:
- Identify the top 3-5 themes across all feedback
- For each theme, note frequency, severity, and a representative quote
- Provide a "bottom line" in 2-3 sentences

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "bottom_line": "string (2-3 sentences)",
  "themes": [
    {{
      "theme": "string",
      "frequency": "High/Medium/Low",
      "severity": 1-5,
      "description": "string (1-2 sentences)",
      "representative_quote": "string"
    }}
  ],
  "overall_sentiment": "Positive/Mixed/Negative",
  "key_metric": "string (e.g., '68% of feedback mentions discovery issues')"
}}

Return ONLY valid JSON.""",
    },
    "pain_points": {
        "name": "Pain Points",
        "description": "Top user frustrations ranked by severity and frequency",
        "prompt_template": """You are a UX researcher analyzing Spotify user feedback for pain points.

TASK: Identify and rank all pain points from the following user feedback.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "pain_points": [
    {{
      "title": "string (short name)",
      "description": "string (2-3 sentences explaining the issue)",
      "category": "Discovery | Recommendations | UI/UX | Performance | Pricing | Social | Content | Other",
      "severity": 1-5,
      "frequency": "number of mentions",
      "affected_segments": ["array of user types"],
      "representative_quotes": ["quote1", "quote2"],
      "potential_impact": "Churn | Reduced Engagement | NPS Drop | Revenue Loss"
    }}
  ],
  "total_pain_mentions": "number",
  "most_severe_category": "string"
}}

Rank by severity × frequency. Return ONLY valid JSON.""",
    },
    "feature_requests": {
        "name": "Feature Requests",
        "description": "Most requested features by frequency and user segment",
        "prompt_template": """You are a Product Manager at Spotify analyzing feature requests from user feedback.

TASK: Extract and categorize all feature requests, ranked by frequency.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "feature_requests": [
    {{
      "title": "string (concise feature name)",
      "description": "string (what users want)",
      "category": "Discovery | Recommendations | UI/UX | Social | Playback | Library | Other",
      "request_count": "number of mentions",
      "user_segments": ["who wants this"],
      "representative_quotes": ["quote1", "quote2"],
      "complexity_estimate": "Low | Medium | High",
      "business_value": "Low | Medium | High"
    }}
  ],
  "total_requests": "number",
  "top_category": "string"
}}

Return ONLY valid JSON.""",
    },
    "positive_feedback": {
        "name": "Positive Feedback",
        "description": "What users love about Spotify — strengths to protect",
        "prompt_template": """You are analyzing what Spotify users love and value most.

TASK: Extract positive feedback themes from the following entries.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "strengths": [
    {{
      "theme": "string",
      "description": "string",
      "frequency": "number of mentions",
      "user_segments": ["who values this"],
      "representative_quotes": ["quote1", "quote2"],
      "strategic_value": "Retention | Acquisition | Differentiation"
    }}
  ],
  "overall_satisfaction_signals": "string (1-2 sentences)",
  "defensible_advantages": ["array of Spotify's key strengths"]
}}

Return ONLY valid JSON.""",
    },
    "negative_feedback": {
        "name": "Negative Feedback",
        "description": "Deep analysis of negative sentiment and root causes",
        "prompt_template": """You are analyzing negative user feedback about Spotify to understand root causes.

TASK: Categorize and analyze all negative feedback.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "negative_themes": [
    {{
      "theme": "string",
      "root_cause": "string (why users feel this way)",
      "frequency": "number of mentions",
      "severity": 1-5,
      "emotional_tone": "Frustration | Anger | Disappointment | Confusion",
      "churn_risk": "Low | Medium | High",
      "representative_quotes": ["quote1", "quote2"]
    }}
  ],
  "churn_signals": ["specific phrases indicating users may leave"],
  "competitor_mentions": ["competitors mentioned positively"]
}}

Return ONLY valid JSON.""",
    },
    "sentiment_analysis": {
        "name": "Sentiment Analysis",
        "description": "Detailed sentiment breakdown across sources and topics",
        "prompt_template": """You are performing sentiment analysis on Spotify user feedback.

TASK: Analyze sentiment distribution across topics and sources.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "overall_sentiment": {{
    "positive_pct": 45,
    "neutral_pct": 30,
    "negative_pct": 25
  }},
  "by_topic": [
    {{
      "topic": "string",
      "positive": 10,
      "neutral": 5,
      "negative": 3,
      "dominant_emotion": "string"
    }}
  ],
  "positive_drivers": ["what makes users happy"],
  "negative_drivers": ["what makes users unhappy"],
  "notable_shifts": "string (any emerging sentiment trends)"
}}

Return ONLY valid JSON.""",
    },
    "competitor_mentions": {
        "name": "Competitor Mentions",
        "description": "References to competing services and switching intent",
        "prompt_template": """You are a competitive intelligence analyst analyzing Spotify user feedback for competitor mentions.

TASK: Extract all references to competing services.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "competitors": [
    {{
      "name": "string (competitor name)",
      "mention_count": "number",
      "sentiment_toward": "Positive | Neutral | Negative",
      "context": "string (why mentioned)",
      "perceived_advantage": "string (what they do better)",
      "representative_quotes": ["quote1", "quote2"]
    }}
  ],
  "switching_signals": [
    {{
      "signal": "string (quote or paraphrase)",
      "from": "Spotify",
      "to": "string (competitor)",
      "reason": "string"
    }}
  ],
  "competitive_advantages_spotify": ["what users still prefer about Spotify"]
}}

Return ONLY valid JSON.""",
    },
    "jobs_to_be_done": {
        "name": "Jobs To Be Done",
        "description": "User jobs, motivations, and outcomes they're hiring Spotify for",
        "prompt_template": """You are a Jobs-to-be-Done researcher analyzing why users "hire" Spotify.

TASK: Extract JTBD statements from user feedback.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "jobs": [
    {{
      "situation": "string (the context/situation triggering the job)",
      "motivation": "string (what the user wants to do)",
      "expected_outcome": "string (the desired outcome)",
      "satisfaction": "Satisfied | Partially Satisfied | Unsatisfied",
      "barriers": ["what prevents job completion"],
      "workarounds": ["what users do instead"],
      "representative_quotes": ["quote1"]
    }}
  ],
  "underserved_jobs": ["jobs Spotify doesn't help with well"],
  "overserved_jobs": ["jobs where Spotify does more than needed"]
}}

Return ONLY valid JSON.""",
    },
    "user_personas": {
        "name": "User Personas",
        "description": "Data-driven user archetypes emerging from feedback patterns",
        "prompt_template": """You are a UX researcher creating data-driven personas from Spotify user feedback.

TASK: Identify distinct user personas from the feedback patterns.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "personas": [
    {{
      "name": "string (creative archetype name)",
      "description": "string (2-3 sentences)",
      "listening_behavior": "string",
      "primary_need": "string",
      "main_frustration": "string",
      "discovery_approach": "string (how they find new music)",
      "churn_risk": "Low | Medium | High",
      "representative_quote": "string",
      "estimated_size": "string (e.g., '20-30% of users')"
    }}
  ],
  "persona_count": "number",
  "most_underserved": "string (which persona is least satisfied)"
}}

Return ONLY valid JSON. Create 3-5 distinct personas.""",
    },
    "theme_clustering": {
        "name": "Theme Clustering",
        "description": "Natural topic clusters found in the feedback data",
        "prompt_template": """You are a qualitative researcher performing thematic analysis on Spotify user feedback.

TASK: Identify natural theme clusters across all feedback.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "clusters": [
    {{
      "theme": "string (cluster name)",
      "sub_themes": ["array of related sub-topics"],
      "review_count": "number in this cluster",
      "sentiment_mix": "Mostly Positive | Mixed | Mostly Negative",
      "key_insight": "string (1 sentence)",
      "representative_quotes": ["quote1", "quote2"]
    }}
  ],
  "cross_cutting_themes": ["themes that appear across multiple clusters"],
  "outlier_feedback": ["unusual feedback that doesn't fit clusters"]
}}

Return ONLY valid JSON.""",
    },
    "emerging_trends": {
        "name": "Emerging Trends",
        "description": "New and growing topics that weren't prominent before",
        "prompt_template": """You are a trend analyst identifying emerging themes in Spotify user feedback.

TASK: Identify feedback themes that appear to be new, growing, or trending.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "trends": [
    {{
      "trend": "string (trend name)",
      "description": "string (what's happening)",
      "growth_signal": "string (why you think it's emerging)",
      "potential_impact": "Low | Medium | High",
      "time_horizon": "Immediate | Short-term | Long-term",
      "related_to": "string (what Spotify feature/change)",
      "representative_quotes": ["quote1"]
    }}
  ],
  "declining_themes": ["topics that seem to be fading"],
  "watch_list": ["topics too early to call but worth monitoring"]
}}

Return ONLY valid JSON.""",
    },
    "product_recommendations": {
        "name": "Product Recommendations",
        "description": "Actionable product suggestions based on feedback patterns",
        "prompt_template": """You are a Senior Product Manager at Spotify turning user feedback into actionable recommendations.

TASK: Generate prioritized product recommendations based on user feedback.

USER FEEDBACK ({review_count} entries from {sources}):
{reviews_text}

OUTPUT FORMAT (JSON):
{{
  "recommendations": [
    {{
      "title": "string (clear action)",
      "description": "string (what to build/fix)",
      "rationale": "string (evidence from feedback)",
      "impact_score": 8,
      "effort_score": 4,
      "confidence_score": 7,
      "ice_score": 14,
      "affected_personas": ["who benefits"],
      "success_metric": "string (how to measure)",
      "representative_quotes": ["supporting evidence"]
    }}
  ],
  "quick_wins": ["high impact, low effort items"],
  "strategic_bets": ["high impact, high effort items"],
  "avoid": ["things users DON'T want"]
}}

IMPORTANT: All score fields (impact_score, effort_score, confidence_score, ice_score) must be numbers, not strings. Calculate ice_score as: impact_score × confidence_score / effort_score (rounded).

Rank by ICE score. Return ONLY valid JSON.""",
    },
}


def get_workflow(workflow_id: str):
    """Get a workflow definition by ID."""
    return WORKFLOWS.get(workflow_id)


def list_workflows():
    """List all available workflows with basic info."""
    return [
        {"id": wid, "name": w["name"], "description": w["description"]}
        for wid, w in WORKFLOWS.items()
    ]
