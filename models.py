"""
SQLAlchemy models: Session, Message, UsageLog.

Schema design:
  - Session: one per onboarding form submission, stores all user context as JSON
  - Message: one row per message (user or model) in a session
  - UsageLog: one row per Gemini API call (not per message pair) — stores real token counts
"""

import json
from datetime import datetime, timezone
from extensions import db


class Session(db.Model):
    """Represents one coaching session, created when a user submits the onboarding form."""

    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    # Stores target_role, experience_level, weak_areas, interview_style, target_company
    onboarding_data = db.Column(db.Text, nullable=False)

    messages = db.relationship(
        "Message", backref="session", lazy=True, cascade="all, delete-orphan"
    )
    usage_logs = db.relationship(
        "UsageLog", backref="session", lazy=True, cascade="all, delete-orphan"
    )

    def get_onboarding_data(self) -> dict:
        """Deserialize onboarding JSON."""
        return json.loads(self.onboarding_data)

    def set_onboarding_data(self, data: dict) -> None:
        """Serialize and store onboarding data."""
        self.onboarding_data = json.dumps(data)

    def __repr__(self):
        return f"<Session id={self.id} created={self.created_at}>"


class Message(db.Model):
    """One chat message — either from the user ('user') or from Gemini ('model')."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # "user" or "model"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Message id={self.id} role={self.role} session={self.session_id}>"


class UsageLog(db.Model):
    """
    One row per Gemini API call.
    Tokens come directly from response.usage_metadata — never hardcoded.
    Cost is computed from published Gemini 3.5 Flash rates.
    """

    __tablename__ = "usage_logs"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    prompt_tokens = db.Column(db.Integer, nullable=False)
    completion_tokens = db.Column(db.Integer, nullable=False)
    total_tokens = db.Column(db.Integer, nullable=False)
    # Stored with 8 decimal places to capture micro-costs accurately
    estimated_cost_usd = db.Column(db.Float, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return (
            f"<UsageLog id={self.id} tokens={self.total_tokens} "
            f"cost=${self.estimated_cost_usd:.8f}>"
        )
