"""
Reports endpoints — list, view, delete, export.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Report, Insight
from schemas import ReportResponse

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    """List all reports."""
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [ReportResponse.model_validate(r, from_attributes=True) for r in reports]


@router.get("/cumulative/all")
def get_cumulative_report(db: Session = Depends(get_db)):
    """
    Get a cumulative report that aggregates insights from ALL past reports.
    For each workflow type, returns the most recent insight.
    Review counts and sources are aggregated across all reports.
    """
    reports = db.query(Report).filter(Report.status == "completed").order_by(Report.created_at.desc()).all()

    if not reports:
        return None

    # Aggregate metadata across all reports
    total_review_count = 0
    all_sources = set()
    all_workflows = set()
    earliest_date = None
    latest_date = None

    for r in reports:
        if r.review_count:
            total_review_count += r.review_count
        if r.sources:
            all_sources.update(r.sources)
        if r.workflows:
            all_workflows.update(r.workflows)
        if r.date_range_start:
            if earliest_date is None or r.date_range_start < earliest_date:
                earliest_date = r.date_range_start
        if r.date_range_end:
            if latest_date is None or r.date_range_end > latest_date:
                latest_date = r.date_range_end

    # For each workflow type, get the MOST RECENT insight (best represents current state)
    workflow_insights = {}
    all_insights = (
        db.query(Insight)
        .filter(Insight.report_id.in_([r.id for r in reports]))
        .order_by(Insight.created_at.desc())
        .all()
    )

    for insight in all_insights:
        wf = insight.workflow
        if wf not in workflow_insights:
            # Take the most recent insight for each workflow as the primary
            workflow_insights[wf] = {
                "id": insight.id,
                "workflow": insight.workflow,
                "title": insight.title,
                "content": insight.content,
                "review_count": total_review_count,
                "ai_model": insight.ai_model,
                "created_at": str(insight.created_at) if insight.created_at else None,
            }

    cumulative = {
        "id": reports[0].id,  # Use latest report ID for reference
        "title": f"Cumulative VoC Report \u2014 {len(reports)} analyses",
        "description": f"Aggregated insights from {total_review_count} reviews across {len(reports)} reports",
        "workflows": sorted(list(all_workflows)),
        "sources": sorted(list(all_sources)),
        "review_count": total_review_count,
        "date_range_start": str(earliest_date) if earliest_date else None,
        "date_range_end": str(latest_date) if latest_date else None,
        "status": "completed",
        "created_at": str(reports[0].created_at) if reports[0].created_at else None,
        "report_count": len(reports),
        "insights": list(workflow_insights.values()),
    }

    return cumulative


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a report with its insights."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "Report not found"}

    insights = (
        db.query(Insight)
        .filter(Insight.report_id == report_id)
        .order_by(Insight.created_at)
        .all()
    )

    return {
        "report": ReportResponse.model_validate(report, from_attributes=True),
        "insights": [
            {
                "id": i.id,
                "workflow": i.workflow,
                "title": i.title,
                "content": i.content,
                "ai_model": i.ai_model,
                "created_at": i.created_at,
            }
            for i in insights
        ],
    }


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report and its insights."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "Report not found"}

    # Delete linked insights
    db.query(Insight).filter(Insight.report_id == report_id).delete()
    db.delete(report)
    db.commit()
    return {"status": "deleted", "id": report_id}


@router.get("/{report_id}/export")
def export_report(report_id: int, db: Session = Depends(get_db)):
    """Export report as JSON."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "Report not found"}

    insights = (
        db.query(Insight)
        .filter(Insight.report_id == report_id)
        .all()
    )

    export_data = {
        "title": report.title,
        "description": report.description,
        "created_at": str(report.created_at),
        "workflows": report.workflows,
        "sources": report.sources,
        "review_count": report.review_count,
        "insights": [
            {
                "workflow": i.workflow,
                "title": i.title,
                "content": i.content,
                "ai_model": i.ai_model,
            }
            for i in insights
        ],
    }

    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.json"},
    )
