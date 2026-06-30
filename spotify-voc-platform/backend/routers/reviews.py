"""
Reviews endpoints — list, search, filter, stats.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional

from database import get_db
from models import Review
from schemas import ReviewsListResponse, ReviewResponse

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.get("", response_model=ReviewsListResponse)
def list_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    """Paginated reviews with filters."""
    query = db.query(Review)

    if source:
        query = query.filter(Review.source == source)
    if sentiment:
        query = query.filter(Review.sentiment == sentiment)
    if rating_min is not None:
        query = query.filter(Review.rating >= rating_min)
    if rating_max is not None:
        query = query.filter(Review.rating <= rating_max)
    if date_from:
        query = query.filter(Review.date >= date_from)
    if date_to:
        query = query.filter(Review.date <= date_to)
    if search:
        query = query.filter(
            or_(
                Review.text_clean.ilike(f"%{search}%"),
                Review.title.ilike(f"%{search}%"),
            )
        )

    total = query.count()

    # Sort
    sort_column = getattr(Review, sort_by, Review.date)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc().nullslast())
    else:
        query = query.order_by(sort_column.asc().nullsfirst())

    # Paginate
    reviews = query.offset((page - 1) * per_page).limit(per_page).all()

    return ReviewsListResponse(
        reviews=[ReviewResponse.model_validate(r, from_attributes=True) for r in reviews],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=max(1, (total + per_page - 1) // per_page),
    )


@router.get("/stats")
def review_stats(db: Session = Depends(get_db)):
    """Aggregate stats for reviews."""
    total = db.query(Review).count()

    sources = (
        db.query(Review.source, func.count(Review.id))
        .group_by(Review.source)
        .all()
    )

    sentiments = (
        db.query(Review.sentiment, func.count(Review.id))
        .filter(Review.sentiment.isnot(None))
        .group_by(Review.sentiment)
        .all()
    )

    avg_rating = db.query(func.avg(Review.rating)).filter(Review.rating.isnot(None)).scalar()

    return {
        "total": total,
        "by_source": {s: c for s, c in sources},
        "by_sentiment": {s: c for s, c in sentiments},
        "average_rating": round(float(avg_rating), 2) if avg_rating else None,
    }


@router.get("/{review_id}")
def get_review(review_id: str, db: Session = Depends(get_db)):
    """Get a single review by ID."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return {"error": "Review not found"}
    return ReviewResponse.model_validate(review, from_attributes=True)


@router.delete("/{review_id}")
def delete_review(review_id: str, db: Session = Depends(get_db)):
    """Delete a review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return {"error": "Review not found"}
    db.delete(review)
    db.commit()
    return {"status": "deleted", "id": review_id}
