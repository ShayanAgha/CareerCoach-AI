"""
Onboarding blueprint.

GET  /  → renders the 5-field onboarding form
POST /  → validates input, creates a Session row, redirects to /chat
"""

from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Session

onboarding_bp = Blueprint("onboarding", __name__)

EXPERIENCE_LEVELS = [
    "Entry-level (0–2 years)",
    "Mid-level (2–5 years)",
    "Senior (5–10 years)",
    "Principal / Staff (10+ years)",
]

INTERVIEW_STYLES = [
    "Behavioral (STAR method)",
    "Technical (algorithms & system design)",
    "Case Study",
    "Mixed (behavioral + technical)",
]


@onboarding_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        target_role = request.form.get("target_role", "").strip()
        experience_level = request.form.get("experience_level", "").strip()
        weak_areas = request.form.get("weak_areas", "").strip()
        interview_style = request.form.get("interview_style", "").strip()
        target_company = request.form.get("target_company", "").strip()

        # Server-side validation
        errors = []
        if not target_role:
            errors.append("Target role is required.")
        if experience_level not in EXPERIENCE_LEVELS:
            errors.append("Please select a valid experience level.")
        if interview_style not in INTERVIEW_STYLES:
            errors.append("Please select a valid interview style.")

        if errors:
            return render_template(
                "onboarding.html",
                errors=errors,
                experience_levels=EXPERIENCE_LEVELS,
                interview_styles=INTERVIEW_STYLES,
                form_data=request.form,
            ), 422

        onboarding_data = {
            "target_role": target_role,
            "experience_level": experience_level,
            "weak_areas": weak_areas or "general interview skills",
            "interview_style": interview_style,
            "target_company": target_company or "a company in your industry",
        }

        coach_session = Session()
        coach_session.set_onboarding_data(onboarding_data)
        db.session.add(coach_session)
        db.session.commit()

        return redirect(url_for("chat.chat_page", session_id=coach_session.id))

    return render_template(
        "onboarding.html",
        errors=[],
        experience_levels=EXPERIENCE_LEVELS,
        interview_styles=INTERVIEW_STYLES,
        form_data={},
    )
