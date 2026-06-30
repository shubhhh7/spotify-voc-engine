"""
Insights endpoints — generate, status, list.
"""
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models import Insight
from schemas import GenerateInsightsRequest, InsightResponse
from services.insight_service import generate_insights, generation_state
from ai.workflows import list_workflows

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


@router.post("/generate")
def start_generate_insights(
    request: GenerateInsightsRequest,
    background_tasks: BackgroundTasks,
):
    """Start generating insights in the background."""
    if generation_state["status"] == "running":
        return {"status": "already_running", "message": "Insight generation is already in progress."}

    # NOTE: Do NOT pass the request-scoped db session to a background task.
    # The background task creates its own session internally.
    background_tasks.add_task(
        generate_insights,
        request.workflows,
        request.sources,
        request.date_from,
        request.date_to,
    )

    return {
        "status": "started",
        "workflows": request.workflows,
        "sources": request.sources,
        "message": f"Generating {len(request.workflows)} insights...",
    }


@router.get("/status")
def get_insight_status():
    """Get current insight generation progress."""
    return generation_state


@router.post("/reset")
def reset_insight_status():
    """Force-reset the generation state if stuck."""
    from services.insight_service import _reset_state
    _reset_state()
    return {"status": "reset", "message": "Generation state has been reset."}


@router.get("/workflows")
def get_available_workflows():
    """List all available AI workflows."""
    return list_workflows()


@router.get("")
def list_insights(
    report_id: Optional[int] = None,
    workflow: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List insights, optionally filtered by report or workflow."""
    query = db.query(Insight)

    if report_id:
        query = query.filter(Insight.report_id == report_id)
    if workflow:
        query = query.filter(Insight.workflow == workflow)

    insights = query.order_by(Insight.created_at.desc()).all()
    return [InsightResponse.model_validate(i, from_attributes=True) for i in insights]


@router.get("/{insight_id}")
def get_insight(insight_id: int, db: Session = Depends(get_db)):
    """Get a single insight."""
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        return {"error": "Insight not found"}
    return InsightResponse.model_validate(insight, from_attributes=True)
