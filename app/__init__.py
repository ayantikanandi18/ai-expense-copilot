import os

from dotenv import load_dotenv
from flask import Flask

from .models import Category, db

DEFAULT_CATEGORIES = [
    "Software & Subscriptions",
    "Travel",
    "Meals & Entertainment",
    "Office Supplies",
    "Payroll & Contractors",
    "Marketing & Advertising",
    "Utilities",
    "Professional Services",
    "Equipment & Hardware",
    "Uncategorized",
]


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-only-not-secure")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "postgresql://copilot:copilot@localhost:5432/expense_copilot"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from . import routes_dashboard, routes_documents, routes_webhook
    app.register_blueprint(routes_dashboard.bp)
    app.register_blueprint(routes_documents.bp)
    app.register_blueprint(routes_webhook.bp)

    with app.app_context():
        db.create_all()
        _seed_categories()

    return app


def _seed_categories():
    existing = {c.name for c in Category.query.all()}
    for name in DEFAULT_CATEGORIES:
        if name not in existing:
            db.session.add(Category(name=name))
    db.session.commit()
