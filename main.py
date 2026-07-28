"""
Flask application entry point.
Run locally with: flask --app main run --debug
Or:               python main.py
"""

import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()  # loads .env before config reads os.environ


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialise extensions
    from extensions import db
    db.init_app(app)

    # Register route blueprints
    from routes.onboarding import onboarding_bp
    from routes.chat import chat_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(onboarding_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(dashboard_bp)

    # Create DB tables (idempotent — safe to call on every startup)
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
