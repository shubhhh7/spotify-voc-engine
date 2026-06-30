"""
Prompt Library for Spotify VoC AI Analysis
Designed for Gemini 1.5 Flash (bulk) and Gemini 1.5 Pro (deep synthesis)

Usage: Import prompts into analyzer scripts.
"""

# ============================================================
# PROMPT 1: STRUCTURED EXTRACTION (Gemini Flash - Bulk)
# ============================================================
# Use this for batches of 20-40 reviews/posts
# Input: Raw text + metadata
# Output: Strict JSON

EXTRACTION_PROMPT = """You are a senior Product Insights analyst at Spotify. Your job is to analyze user feedback and extract structured insights.

TASK: Analyze the following user feedback entries and extract structured data for each.

INSTRUCTIONS:
1. Read each entry carefully. Consider both explicit complaints and implicit frustrations.
2. For each entry, output a JSON object with these exact fields:
   - "pain_point": boolean (true if user expresses clear frustration or unmet need)
   - "pain_category": string, one of: [Discovery, Recommendations, UI/UX, Performance, Pricing, Social, Content, Other, None]
   - "pain_severity": integer 1-5 (1=mild annoyance, 5=dealbreaker causing churn)
   - "sentiment": string, one of: [Very Negative, Negative, Neutral, Positive, Very Positive]
   - "emotion": string, one of: [Frustration, Confusion, Anger, Disappointment, Indifference, Satisfaction, Excitement, Anxiety, Boredom, None]
   - "jtbd_statement": string, complete the sentence: "When I [situation], I want to [motivation], so I can [outcome]." Use user's own words where possible. If no JTBD is clear, use "Unclear".
   - "discovery_issue": boolean (true if about struggling to find new music)
   - "recommendation_issue": boolean (true if about bad recommendations)
   - "repetition_issue": boolean (true if about hearing same songs/artists repeatedly)
   - "unmet_need": string, max 15 words. What does the user want that Spotify doesn't provide?
   - "user_segment_hint": string, one of: [Casual Listener, Power User, Curator, Social Listener, New User, Long-term User, Mobile-only, Desktop-heavy, Commuter, Student, None]
   - "key_quote": string, exact quote from text that best captures the core issue (max 20 words)
   - "confidence": integer 1-5 (how confident are you in this extraction?)

3. Be precise. Do not hallucinate categories. If unclear, use "None" or "Unclear".
4. Return ONLY a JSON array. No markdown, no explanations, no code blocks.

USER FEEDBACK ENTRIES:
{entries}

OUTPUT FORMAT:
[{{"id": "entry_1", "pain_point": true, ...}}, {{"id": "entry_2", ...}}]
"""

# ============================================================
# PROMPT 2: DEEP JTBD EXTRACTION (Gemini Pro - Individual)
# ============================================================
# Use this for long Reddit posts (>200 words) or detailed reviews
# Input: Single long-form text
# Output: Rich JSON

JTBD_DEEP_PROMPT = """You are a Jobs-to-be-Done researcher specializing in music consumption behavior.

TASK: Analyze this detailed user feedback and extract the deep Jobs-to-be-Done, emotional triggers, and behavioral context.

USER FEEDBACK:
{text}

METADATA:
Source: {source}
Rating/Score: {rating}
Date: {date}

OUTPUT JSON with these fields:
- "main_jtbd": The primary job this user hired Spotify to do (format: "When I [situation], I want to [motivation], so I can [outcome]")
- "secondary_jtbd": Additional jobs (array of strings, max 3)
- "emotional_trigger": What emotion drove them to write this? (string)
- "before_state": What was their experience/situation before this issue? (string, 1-2 sentences)
- "after_state": What do they want their experience to be? (string, 1-2 sentences)
- "struggle_moment": The specific moment when Spotify failed them (string, be precise)
- "workarounds": What are they doing instead? (array of strings)
- "switching_triggers": What would make them switch to Apple Music/YouTube Music/etc? (array of strings)
- "progress_how": How do they measure if Spotify is helping them make progress? (string)
- "social_context": Who else is involved in their listening? (string: "Solo", "Social", "Family", "Partner", "Communal")
- "listening_context": Where/when do they listen? (string: "Commute", "Work", "Exercise", "Sleep", "Study", "Party", "Chores", "Background")
- "content_preference": What type of content do they prefer? (string: "Playlists", "Albums", "Radio", "Podcasts", "Mixes", "Artist Radio")
- "discovery_behavior": How do they currently discover music? (string)
- "discovery_framer": How do they FRAME the discovery problem? (string: "Spotify doesn't show me X", "I don't know how to find X", "Algorithm is Y", "I miss Z feature")
- "pain_intensity": 1-10 scale
- "churn_risk": "Low", "Medium", "High", or "Very High"
- "evidence_quote": The most powerful exact quote from the text (max 30 words)

Return ONLY valid JSON. No markdown.
"""

# ============================================================
# PROMPT 3: CROSS-SOURCE THEME SYNTHESIS (Gemini Pro)
# ============================================================
# Input: Aggregated theme data from all sources
# Output: Strategic insights

SYNTHESIS_PROMPT = """You are the VP of Product Insights at Spotify. You are presenting findings to the C-suite about music discovery and user satisfaction.

TASK: Synthesize the following aggregated user feedback data into strategic insights.

DATA SUMMARY:
{data_summary}

TOP THEMES BY FREQUENCY:
{themes}

TOP JTBDs:
{jtbd_list}

USER SEGMENT SIGNALS:
{segment_signals}

OUTPUT FORMAT - JSON with these sections:

1. "executive_summary": 3 bullet points, max 30 words each. What must leadership know?

2. "strategic_insights": Array of 5-7 objects, each with:
   - "insight": The insight statement (bold, contrarian where possible)
   - "evidence": "Based on X mentions from Y sources, particularly [specific quote]"
   - "confidence": "High", "Medium", or "Low"
   - "business_impact": "Revenue", "Retention", "Engagement", or "Acquisition"
   - "severity": 1-10
   - "affected_segments": Array of user segments
   - "so_what": "Therefore, Spotify should..." (specific, actionable implication)

3. "discovery_problems": Array of objects answering "Why do users struggle to discover new music?"
   Each with: "problem", "root_cause", "user_evidence", "frequency"

4. "recommendation_frustrations": Array of objects answering "What are the most common frustrations with recommendations?"
   Each with: "frustration", "scenario", "frequency", "emotional_tone"

5. "behavioral_patterns": Array of objects answering "What listening behaviors are users trying to achieve?"
   Each with: "behavior", "jtbd", "barrier", "workaround"

6. "repetition_causes": Array of objects answering "What causes users to repeatedly listen to the same content?"
   Each with: "cause", "psychology", "frequency", "segment"

7. "segment_profiles": Array of 3-4 distinct user segments experiencing different discovery challenges
   Each with: "name", "description", "key_pain", "discovery_behavior", "unmet_need", "quote"

8. "unmet_needs": Array of consistent unmet needs across sources
   Each with: "need", "frequency", "current_workaround", "opportunity_size"

9. "opportunity_scoring": Array of top 5 opportunities ranked by:
   - "opportunity": What should Spotify build/fix?
   - "impact": 1-10 (user + business)
   - "effort": 1-10 (technical + organizational)
   - "confidence": 1-10 (evidence strength)
   - "ice_score": Impact × Confidence / Effort (calculate this)
   - "rationale": Why this score?

10. "counter_evidence": What evidence contradicts our main narrative? (array of strings)

11. "falsification_conditions": "We would be wrong if..." (array of 3 strings)

Return ONLY valid JSON. No markdown, no commentary.
"""

# ============================================================
# PROMPT 4: COMPETITIVE IMPLICATION (Gemini Pro)
# ============================================================

COMPETITIVE_PROMPT = """You are a competitive intelligence analyst. Given these user complaints about Spotify, infer what competitors might be doing better or what users are switching to.

USER COMPLAINTS:
{complaints}

OUTPUT JSON:
- "competitive_threats": Array of 3-5 threats (e.g., "Apple Music's human curation", "TikTok's discovery", "YouTube's variety")
- "switching_signals": What specific behaviors indicate switching? (array)
- "defensible_advantages": What does Spotify still do well that users mention? (array)
- "vulnerable_areas": Where is Spotify most vulnerable? (array with severity scores)
- "recommended_response": Strategic response per vulnerable area (array)

Return ONLY valid JSON.
"""

# ============================================================
# PROMPT 5: HALLUCINATION AUDIT (Self-check)
# ============================================================
# Use this to verify AI outputs against source text

AUDIT_PROMPT = """You are a quality auditor. Verify if the following AI-generated insight is actually supported by the source text.

SOURCE TEXT:
{source_text}

AI INSIGHT:
{ai_insight}

TASK: Return JSON with:
- "is_supported": boolean
- "supporting_evidence": exact quote from source that supports the insight (or "None")
- "contradicting_evidence": exact quote that contradicts it (or "None")
- "confidence": 1-5 (how well supported)
- "issues": Array of any hallucinations, exaggerations, or misinterpretations

Return ONLY valid JSON.
"""

# ============================================================
# PROMPT 6: FINAL REPORT NARRATIVE (Gemini Pro)
# ============================================================
# Generate the final presentation narrative

REPORT_PROMPT = """You are a Senior Product Manager presenting a VoC research readout to Spotify leadership.

RESEARCH CONTEXT:
- Analyzed {volume} user feedback entries from {sources}
- Time period: Recent 12 months
- Focus: Music discovery, recommendations, listening behavior

SYNTHESIZED INSIGHTS:
{insights}

TASK: Write a compelling 2-page executive report with this structure:

1. "bottom_line_up_front": 3 sentences. The most important finding and what we should do about it.

2. "what_we_heard": Narrative section (300 words) describing the user reality. Use specific quotes. Make it visceral.

3. "the_data": Key statistics presented as evidence (bullet points with numbers)

4. "the_segments": 3 distinct user archetypes with names, quotes, and behaviors

5. "the_opportunities": 5 ranked opportunities with ICE scores and 1-sentence rationale each

6. "the_risks": What happens if we don't act? (3 bullets, be specific about business impact)

7. "recommended_next_steps": 3 specific, time-bound research or product actions

8. "appendix": Methodology note (2 sentences on data sources and limitations)

WRITING STYLE:
- Direct, no fluff, no buzzwords
- Every claim anchored to specific user evidence
- Appropriate confidence levels (don't overstate)
- Contrarian insights highlighted
- Write like a top-tier consulting firm + product intuition

Return as plain text with clear headers. No markdown code blocks.
"""

__all__ = [
    "EXTRACTION_PROMPT",
    "JTBD_DEEP_PROMPT", 
    "SYNTHESIS_PROMPT",
    "COMPETITIVE_PROMPT",
    "AUDIT_PROMPT",
    "REPORT_PROMPT"
]
