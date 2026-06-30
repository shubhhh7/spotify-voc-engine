"""
Cleaning Service — applies text normalization and classification to reviews.
Lightweight version of the original 4_data_cleaner.py for real-time use.
"""
import re
from sqlalchemy.orm import Session
from models import Review


# Contractions to expand
CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "don't": "do not",
    "doesn't": "does not", "didn't": "did not", "isn't": "is not",
    "wasn't": "was not", "aren't": "are not", "weren't": "were not",
    "hasn't": "has not", "haven't": "have not", "couldn't": "could not",
    "wouldn't": "would not", "shouldn't": "should not",
    "i'm": "i am", "you're": "you are", "they're": "they are",
    "it's": "it is", "that's": "that is", "there's": "there is",
    "i've": "i have", "we've": "we have", "they've": "they have",
    "i'll": "i will", "you'll": "you will", "we'll": "we will",
    "i'd": "i would", "you'd": "you would", "we'd": "we would",
    "gonna": "going to", "wanna": "want to", "gotta": "got to",
}

# Keywords for relevance classification
RELEVANT_KEYWORDS = [
    "discover", "recommendation", "playlist", "algorithm", "radio",
    "daily mix", "discover weekly", "release radar", "shuffle",
    "repeat", "same song", "new music", "music taste", "personali",
    "suggestion", "curate", "genre", "mood", "similar artist",
    "exploration", "variety", "diversity", "fresh", "stale",
    "bubble", "echo chamber", "ai dj", "blend", "autoplay",
]

PRODUCT_TERMS = [
    "discover weekly", "daily mix", "smart shuffle", "ai dj",
    "release radar", "radio", "blend", "liked songs", "premium",
    "recommendations", "algorithm", "playlist", "wrapped", "daylist",
]


def clean_text(text: str) -> str:
    """Normalize text for analysis."""
    if not text or not text.strip():
        return ""

    # Fix unicode
    text = text.encode("utf-8", "ignore").decode("utf-8")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2014", " - ").replace("\xa0", " ")

    # Remove URLs
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|%[0-9a-fA-F]{2})+",
        "[URL]", text
    )

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Cap repeated punctuation
    text = re.sub(r"([!?])\1{2,}", r"\1\1", text)

    # Lowercase
    text = text.lower().strip()

    # Expand contractions
    for contraction, expansion in CONTRACTIONS.items():
        text = re.sub(r"\b" + re.escape(contraction) + r"\b", expansion, text)

    return text.strip()


def classify_sentiment_simple(text: str, rating: float = None) -> str:
    """Basic rule-based sentiment classification."""
    if rating is not None:
        if rating <= 2:
            return "negative"
        elif rating >= 4:
            return "positive"
        else:
            return "neutral"

    # Text-based fallback
    text_lower = text.lower() if text else ""
    negative_words = ["terrible", "awful", "worst", "hate", "broken", "frustrat",
                      "annoying", "useless", "waste", "disappoint", "uninstall"]
    positive_words = ["love", "great", "amazing", "perfect", "awesome", "best",
                      "excellent", "fantastic", "wonderful", "helpful"]

    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)

    if neg_count > pos_count:
        return "negative"
    elif pos_count > neg_count:
        return "positive"
    return "neutral"


def classify_relevance(text: str) -> str:
    """Classify review relevance to music discovery research."""
    if not text:
        return "not_relevant"
    text_lower = text.lower()

    has_relevant = any(kw in text_lower for kw in RELEVANT_KEYWORDS)
    has_product = any(term in text_lower for term in PRODUCT_TERMS)

    if has_relevant or has_product:
        return "relevant"
    if "spotify" in text_lower or "music" in text_lower:
        return "partially_relevant"
    return "not_relevant"


def compute_quality_score(text: str) -> int:
    """Score 0-100 based on information richness."""
    if not text:
        return 0
    score = 0
    words = text.split()
    word_count = len(words)

    # Length (0-25)
    if word_count >= 50:
        score += 25
    elif word_count >= 20:
        score += 15
    elif word_count >= 10:
        score += 8
    else:
        score += 3

    # Product mentions (0-25)
    product_mentions = sum(1 for term in PRODUCT_TERMS if term in text.lower())
    score += min(product_mentions * 5, 25)

    # Actionable language (0-25)
    actionable = ["should", "would be better", "wish", "need", "want",
                  "please", "fix", "improve", "add", "remove", "change",
                  "why does", "used to", "bring back"]
    actionable_count = sum(1 for p in actionable if p in text.lower())
    score += min(actionable_count * 5, 25)

    # Emotion (0-15)
    emotion = ["!", "?", "frustrat", "love", "hate", "terrible", "disappoint", "annoy"]
    emotion_count = sum(1 for e in emotion if e in text.lower())
    score += min(emotion_count * 3, 15)

    # Detail (0-10)
    if any(c.isdigit() for c in text):
        score += 3
    if "because" in text.lower() or "since" in text.lower():
        score += 4
    if "example" in text.lower():
        score += 3

    return min(score, 100)


def clean_reviews_for_run(db: Session, scrape_run_id: int) -> int:
    """
    Clean all reviews from a scrape run.
    Sets text_clean, sentiment, quality_score, relevance.
    Returns number of reviews processed.
    """
    reviews = (
        db.query(Review)
        .filter(Review.scrape_run_id == scrape_run_id)
        .filter(Review.text_clean.is_(None))
        .all()
    )

    count = 0
    for review in reviews:
        text = review.text_original or ""
        review.text_clean = clean_text(text)
        review.sentiment = classify_sentiment_simple(review.text_clean, review.rating)
        review.quality_score = compute_quality_score(review.text_clean)
        review.relevance = classify_relevance(review.text_clean)
        count += 1

    if count > 0:
        db.commit()

    return count


def clean_all_uncleaned(db: Session) -> int:
    """Clean any reviews that don't have text_clean set yet."""
    reviews = (
        db.query(Review)
        .filter(Review.text_clean.is_(None))
        .limit(500)
        .all()
    )

    count = 0
    for review in reviews:
        text = review.text_original or ""
        review.text_clean = clean_text(text)
        review.sentiment = classify_sentiment_simple(review.text_clean, review.rating)
        review.quality_score = compute_quality_score(review.text_clean)
        review.relevance = classify_relevance(review.text_clean)
        count += 1

    if count > 0:
        db.commit()

    return count
