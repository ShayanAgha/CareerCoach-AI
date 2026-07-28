"""
Chat blueprint.

GET  /chat?session_id=<id>  → renders the chat UI with full message history
POST /chat                  → receives JSON {session_id, message}, calls Gemini,
                              saves Message + UsageLog rows, returns JSON reply
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from extensions import db
from models import Session, Message, UsageLog
from gemini_client import build_system_prompt, call_gemini, compute_cost

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["GET"])
def chat_page():
    session_id = request.args.get("session_id", type=int)
    if not session_id:
        return redirect(url_for("onboarding.index"))

    coach_session = Session.query.get_or_404(session_id)
    onboarding = coach_session.get_onboarding_data()
    messages = (
        Message.query.filter_by(session_id=session_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return render_template(
        "chat.html",
        coach_session=coach_session,
        onboarding=onboarding,
        messages=messages,
        session_id=session_id,
    )


@chat_bp.route("/chat", methods=["POST"])
def send_message():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    user_message = (data.get("message") or "").strip()

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    if not user_message:
        return jsonify({"error": "message cannot be empty"}), 400

    coach_session = Session.query.get(session_id)
    if not coach_session:
        return jsonify({"error": "Session not found. Start a new session."}), 404

    # Build personalised system prompt from this session's onboarding data
    onboarding_data = coach_session.get_onboarding_data()
    system_prompt = build_system_prompt(onboarding_data)

    # Persist user message first (so it's included in the history sent to Gemini)
    user_msg = Message(session_id=session_id, role="user", content=user_message)
    db.session.add(user_msg)
    db.session.flush()  # get DB id without committing yet

    # Pull FULL conversation history — this is what makes the bot multi-turn.
    # Every call to Gemini receives all prior messages, so prompt_token_count
    # grows with conversation length. That's the intended behaviour.
    all_messages = (
        Message.query.filter_by(session_id=session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    history = [{"role": msg.role, "content": msg.content} for msg in all_messages]

    try:
        reply_text, usage_metadata = call_gemini(history, system_prompt)
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Gemini API error: {exc}"}), 500

    # Persist model reply
    model_msg = Message(session_id=session_id, role="model", content=reply_text)
    db.session.add(model_msg)

    # Compute cost from REAL usage_metadata — never hardcoded
    cost_data = compute_cost(usage_metadata)

    # One UsageLog row per API call (assignment spec: not per message pair)
    usage_log = UsageLog(
        session_id=session_id,
        prompt_tokens=cost_data["prompt_tokens"],
        completion_tokens=cost_data["completion_tokens"],
        total_tokens=cost_data["total_tokens"],
        estimated_cost_usd=cost_data["estimated_cost_usd"],
    )
    db.session.add(usage_log)
    db.session.commit()

    return jsonify(
        {
            "reply": reply_text,
            "tokens": {
                "prompt": cost_data["prompt_tokens"],
                "completion": cost_data["completion_tokens"],
                "total": cost_data["total_tokens"],
            },
            "cost_usd": cost_data["estimated_cost_usd"],
        }
    )
