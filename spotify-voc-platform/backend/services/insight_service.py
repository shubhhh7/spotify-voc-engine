"""
Insight generation service — orchestrates AI workflows against review data.

Strategy: Process each source in small chunks to avoid Groq payload-too-large errors.
- Reddit, community, social posts → max 10 reviews per chunk (longer text)
- App Store, Play Store → max 15 reviews per chunk (shorter text)
- Twitter → max 20 reviews per chunk (shortest text)
- Each review truncated to 400 chars max
- If a source has many reviews, we process multiple chunks and merge results
"""
import json
import time
import logging
from datetime import datetime

from sqlalchemy import and_

from models import Review, Insight, Report
from ai.workflows import WORKFLOWS
from services.llm_provider import generate_with_metadata

logger = logging.getLogger(__name__)

# Chunk sizes per source - keeps payload small for Groq
SOURCE_CHUNK_SIZES = {
    "reddit": 8,
    "spotify_community": 8,
    "hackernews": 8,
    "lemmy": 8,
    "social": 8,
    "twitter": 15,
    "app_store": 12,
    "play_store": 12,
}
DEFAULT_CHUNK_SIZE = 8

# Max characters per individual review text
MAX_REVIEW_TEXT_LENGTH = 350

# Max total characters for the reviews block in a single API call
MAX_PAYLOAD_CHARS = 6000

# Delay between API calls to avoid Groq 429 (seconds)
DELAY_BETWEEN_CALLS = 2.0

# Max chunks per source per workflow (limits total API calls)
MAX_CHUNKS_PER_SOURCE = 2

# In-memory progress state (single-user tool)
generation_state = {
    "status": "idle",
    "workflows_total": 0,
    "workflows_completed": 0,
    "current_workflow": None,
    "current_step": None,
    "errors": [],
}


def _reset_state():
    generation_state["status"] = "idle"
    generation_state["workflows_total"] = 0
    generation_state["workflows_completed"] = 0
    generation_state["current_workflow"] = None
    generation_state["current_step"] = None
    generation_state["errors"] = []


def _get_chunk_size(source: str) -> int:
    """Get appropriate chunk size for a source type."""
    source_lower = (source or "").lower().replace(" ", "_")
    for key, size in SOURCE_CHUNK_SIZES.items():
        if key in source_lower:
            return size
    return DEFAULT_CHUNK_SIZE


def _truncate_text(text: str, max_len: int = MAX_REVIEW_TEXT_LENGTH) -> str:
    """Truncate review text to keep payloads small."""
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _build_reviews_text_chunked(reviews: list[Review], max_chars: int = MAX_PAYLOAD_CHARS) -> str:
    """Build a text block from reviews, hard-capped at max_chars.
    Each review is truncated individually, and we stop adding once we hit the limit."""
    entries = []
    total_chars = 0

    for i, review in enumerate(reviews):
        text = review.text_clean or review.text_original or ""
        if not text.strip():
            continue

        # Truncate individual reviews
        text = _truncate_text(text)

        entry = f"[{i+1}] Source: {review.source}"
        if review.rating:
            entry += f" | Rating: {review.rating}"
        entry += f"\n{text}\n"

        if total_chars + len(entry) > max_chars:
            break

        entries.append(entry)
        total_chars += len(entry)

    return "\n".join(entries)


def _get_source_names(sources: list[str]) -> str:
    """Convert source IDs to readable names."""
    names = {
        "reddit": "Reddit",
        "app_store": "App Store",
        "play_store": "Play Store",
        "spotify_community": "Spotify Community",
        "social": "Social Media",
        "twitter": "Twitter/X",
        "hackernews": "Hacker News",
        "lemmy": "Lemmy",
    }
    return ", ".join(names.get(s, s) for s in sources)


def _call_ai_safe(prompt: str, workflow_name: str) -> tuple:
    """
    Call the multi-provider LLM service. Returns (result, model_used).
    Automatically handles failover across Gemini → Groq → Cerebras → OpenRouter.
    """
    try:
        result, model_used = generate_with_metadata(prompt)
        return result, model_used
    except Exception as e:
        logger.error(f"All LLM providers failed for {workflow_name}: {e}")
        return {"error": f"AI unavailable: {str(e)}", "status": "ai_error"}, "none"


def _merge_chunk_results(chunk_results: list[dict]) -> dict:
    """Merge multiple chunk results into one combined insight.
    Combines arrays and takes the most common/severe values."""
    if not chunk_results:
        return {}
    if len(chunk_results) == 1:
        return chunk_results[0]

    # Deep merge strategy: concatenate arrays, keep first scalar values
    merged = {}
    for result in chunk_results:
        if not isinstance(result, dict):
            continue
        for key, value in result.items():
            if key == "parse_error" or key == "raw_response":
                continue
            if key not in merged:
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                merged[key].extend(value)
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                # Merge nested dicts
                for k, v in value.items():
                    if k not in merged[key]:
                        merged[key][k] = v
                    elif isinstance(v, list) and isinstance(merged[key][k], list):
                        merged[key][k].extend(v)

    # Deduplicate and limit arrays to prevent oversized results
    for key, value in merged.items():
        if isinstance(value, list) and len(value) > 15:
            # Keep top items (they came from most severe/frequent chunks)
            merged[key] = value[:15]

    return merged


def _group_reviews_by_source(reviews: list[Review]) -> dict:
    """Group reviews by their source type."""
    groups = {}
    for review in reviews:
        source = review.source or "unknown"
        if source not in groups:
            groups[source] = []
        groups[source].append(review)
    return groups


def generate_insights(
    workflows: list,
    sources: list,
    date_from=None,
    date_to=None,
):
    """
    Generate insights for the given workflows and return the report ID.

    Only processes reviews that haven't been analyzed yet (last_analyzed_at IS NULL).
    After successful analysis, marks those reviews so they won't be re-processed.

    Strategy: For each workflow, process reviews in small per-source chunks
    through Groq, then merge the results. This avoids payload-too-large errors.

    NOTE: This runs as a background task, so it creates its own DB session
    rather than receiving one from the request (which would be closed).
    """
    from database import SessionLocal

    _reset_state()
    generation_state["status"] = "running"
    generation_state["workflows_total"] = len(workflows)

    db = SessionLocal()

    try:
        # Query only UNPROCESSED reviews (last_analyzed_at is NULL)
        generation_state["current_step"] = "Querying new reviews..."
        query = db.query(Review).filter(Review.last_analyzed_at.is_(None))

        if sources:
            query = query.filter(Review.source.in_(sources))
        if date_from:
            query = query.filter(Review.date >= date_from)
        if date_to:
            query = query.filter(Review.date <= date_to)

        # Prefer cleaned reviews, most recent first
        reviews = (
            query
            .filter(Review.text_clean.isnot(None))
            .order_by(Review.date.desc().nullslast())
            .limit(200)
            .all()
        )

        if not reviews:
            # Fallback to uncleaned but still unprocessed
            reviews = (
                db.query(Review)
                .filter(Review.last_analyzed_at.is_(None))
                .filter(Review.source.in_(sources) if sources else True)
                .order_by(Review.date.desc().nullslast())
                .limit(200)
                .all()
            )

        if not reviews:
            generation_state["status"] = "failed"
            generation_state["errors"].append(
                "No new unprocessed reviews found. All reviews have already been analyzed."
            )
            return 0

        review_count = len(reviews)
        source_names = _get_source_names(sources) if sources else "All Sources"

        # Keep track of review IDs so we can mark them as analyzed after success
        processed_review_ids = [r.id for r in reviews]

        # Group reviews by source for chunked processing
        source_groups = _group_reviews_by_source(reviews)
        logger.info(f"Processing {review_count} NEW reviews from sources: {list(source_groups.keys())}")

        # Create report
        report = Report(
            title=f"VoC Insights — {datetime.utcnow().strftime('%B %d, %Y')}",
            description=f"Generated from {review_count} new reviews across {source_names}",
            workflows=workflows,
            sources=sources,
            review_count=review_count,
            date_range_start=reviews[-1].date if reviews[-1].date else None,
            date_range_end=reviews[0].date if reviews[0].date else None,
            status="generating",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # Run each workflow
        for i, workflow_id in enumerate(workflows):
            workflow = WORKFLOWS.get(workflow_id)
            if not workflow:
                generation_state["errors"].append(f"Unknown workflow: {workflow_id}")
                continue

            generation_state["current_workflow"] = workflow["name"]
            generation_state["current_step"] = f"Generating {workflow['name']}..."
            logger.info(f"Running workflow: {workflow_id} ({i+1}/{len(workflows)})")

            try:
                chunk_results = []

                # Process each source in appropriately-sized chunks
                for source, source_reviews in source_groups.items():
                    chunk_size = _get_chunk_size(source)
                    total_source_reviews = len(source_reviews)

                    # Limit reviews per source — only process MAX_CHUNKS_PER_SOURCE chunks
                    max_reviews_per_source = min(total_source_reviews, chunk_size * MAX_CHUNKS_PER_SOURCE)
                    source_reviews_limited = source_reviews[:max_reviews_per_source]

                    generation_state["current_step"] = (
                        f"Generating {workflow['name']} — {source} "
                        f"({len(source_reviews_limited)} reviews, chunks of {chunk_size})..."
                    )

                    # Process in chunks with delay between calls
                    chunks_sent = 0
                    for chunk_start in range(0, len(source_reviews_limited), chunk_size):
                        if chunks_sent >= MAX_CHUNKS_PER_SOURCE:
                            break

                        chunk = source_reviews_limited[chunk_start:chunk_start + chunk_size]
                        reviews_text = _build_reviews_text_chunked(chunk)

                        if not reviews_text.strip():
                            continue

                        # Delay between API calls to avoid rate limiting
                        if chunks_sent > 0 or len(chunk_results) > 0:
                            time.sleep(DELAY_BETWEEN_CALLS)

                        # Build prompt with this small chunk
                        prompt = workflow["prompt_template"].format(
                            review_count=len(chunk),
                            sources=source,
                            reviews_text=reviews_text,
                        )

                        # Call AI with safety
                        result, model_used = _call_ai_safe(prompt, workflow["name"])

                        if result and isinstance(result, dict) and "error" not in result:
                            chunk_results.append(result)

                        chunks_sent += 1

                # Merge all chunk results into one combined insight
                if chunk_results:
                    merged_result = _merge_chunk_results(chunk_results)
                    ai_model_used = model_used  # From last successful call
                else:
                    merged_result = {"error": "No results from any chunk", "status": "empty"}
                    ai_model_used = "none"

                # Store insight
                insight = Insight(
                    workflow=workflow_id,
                    title=workflow["name"],
                    content=merged_result if isinstance(merged_result, dict) else {"data": merged_result},
                    sources_used=sources,
                    review_count=review_count,
                    date_range_start=report.date_range_start,
                    date_range_end=report.date_range_end,
                    ai_model=ai_model_used,
                    report_id=report.id,
                )
                db.add(insight)
                db.commit()

            except Exception as e:
                logger.error(f"Workflow {workflow_id} failed: {e}")
                generation_state["errors"].append(f"{workflow['name']}: {str(e)}")

                # Store error as insight so user sees partial results
                insight = Insight(
                    workflow=workflow_id,
                    title=f"{workflow['name']} (Failed)",
                    content={"error": str(e), "status": "failed"},
                    sources_used=sources,
                    review_count=review_count,
                    ai_model="none",
                    report_id=report.id,
                )
                db.add(insight)
                db.commit()

            generation_state["workflows_completed"] = i + 1

        # Mark all processed reviews as analyzed so they won't be re-processed
        now = datetime.utcnow()
        db.query(Review).filter(Review.id.in_(processed_review_ids)).update(
            {Review.last_analyzed_at: now},
            synchronize_session=False,
        )

        # Mark report complete
        report.status = "completed"
        db.commit()

        generation_state["status"] = "completed"
        generation_state["current_workflow"] = None
        generation_state["current_step"] = "Done"

        logger.info(f"Report {report.id} completed with {len(workflows)} workflows, marked {len(processed_review_ids)} reviews as analyzed")
        return report.id

    except Exception as e:
        # Catch-all: ensure state never stays stuck at "running"
        logger.error(f"Insight generation failed with unhandled error: {e}", exc_info=True)
        generation_state["status"] = "failed"
        generation_state["current_step"] = f"Failed: {str(e)}"
        generation_state["errors"].append(f"Unhandled error: {str(e)}")
        return 0

    finally:
        db.close()
