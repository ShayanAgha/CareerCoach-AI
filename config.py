"""
Application configuration.
Reads all secrets from environment variables.
Local dev: uses .env file via python-dotenv (loaded in main.py).
"""

import os


class Config:
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database — SQLite for local dev via SQLAlchemy
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(_base_dir, "instance", "app.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
