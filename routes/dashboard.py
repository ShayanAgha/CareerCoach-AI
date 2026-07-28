"""
Dashboard blueprint.

GET /dashboard?session_id=<id>  → renders per-session usage dashboard
GET /api/usage?session_id=<id>  → JSON: aggregates + per-call breakdown
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from extensions import db
from models import Session, UsageLog
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)


def _get_aggregates(session_id: int):
    """Return aggregate usage stats for one session."""
    return db.session.query(
        func.count(UsageLog.id).label("total_requests"),
        func.sum(UsageLog.prompt_tokens).label("total_input_tokens"),
        func.sum(UsageLog.completion_tokens).label("total_output_tokens"),
        func.sum(UsageLog.total_tokens).label("total_tokens"),
        func.sum(UsageLog.estimated_cost_usd).label("total_cost"),
    ).filter(UsageLog.session_id == session_id).first()


@dashboard_bp.route("/dashboard")
def dashboard():
    session_id = request.args.get("session_id", type=int)
    if not session_id:
        return redirect(url_for("onboarding.index"))

    coach_session = Session.query.get_or_404(session_id)
    onboarding = coach_session.get_onboarding_data()
    usage_logs = (
        UsageLog.query.filter_by(session_id=session_id)
        .order_by(UsageLog.created_at.asc())
        .all()
    )
    totals = _get_aggregates(session_id)

    return render_template(
        "dashboard.html",
        coach_session=coach_session,
        onboarding=onboarding,
        usage_logs=usage_logs,
        totals=totals,
        session_id=session_id,
    )


@dashboard_bp.route("/api/usage")
def api_usage():
    """JSON endpoint backing the dashboard. Returns aggregates + per-call breakdown."""
    session_id = request.args.get("session_id", type=int)
    if not session_id:
        return jsonify({"error": "session_id query parameter is required"}), 400

    coach_session = Session.query.get(session_id)
    if not coach_session:
        return jsonify({"error": "Session not found"}), 404

    usage_logs = (
        UsageLog.query.filter_by(session_id=session_id)
        .order_by(UsageLog.created_at.asc())
        .all()
    )
    totals = _get_aggregates(session_id)

    return jsonify(
        {
            "session_id": session_id,
            "model": "gemini-3.5-flash",
            "pricing": {
                "input_per_1m_usd": 0.30,
                "output_per_1m_usd": 2.50,
                "source": "https://ai.google.dev/gemini-api/docs/pricing",
                "as_of": "July 2026",
            },
            "aggregates": {
                "total_requests": totals.total_requests or 0,
                "total_input_tokens": int(totals.total_input_tokens or 0),
                "total_output_tokens": int(totals.total_output_tokens or 0),
                "total_tokens": int(totals.total_tokens or 0),
                "total_cost_usd": round(float(totals.total_cost or 0), 8),
            },
            "calls": [
                {
                    "id": log.id,
                    "created_at": log.created_at.isoformat() + "Z",
                    "prompt_tokens": log.prompt_tokens,
                    "completion_tokens": log.completion_tokens,
                    "total_tokens": log.total_tokens,
                    "estimated_cost_usd": log.estimated_cost_usd,
                }
                for log in usage_logs
            ],
        }
    )
