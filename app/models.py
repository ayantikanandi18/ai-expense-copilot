from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def now_utc():
    return datetime.now(timezone.utc)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Category {self.name}>"


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(20), nullable=False, default="upload")  # upload | webhook
    vendor = db.Column(db.String(200))
    document_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(12, 2))
    raw_text = db.Column(db.Text, nullable=False)
    redacted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)

    line_items = db.relationship("LineItem", backref="document", cascade="all, delete-orphan")


class LineItem(db.Model):
    __tablename__ = "line_items"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    amount = db.Column(db.Numeric(12, 2))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    confidence = db.Column(db.Float)
    rationale = db.Column(db.Text)

    category = db.relationship("Category")


class MonthlyTotal(db.Model):
    """Aggregated actuals per category per month — the input to forecasting.py."""

    __tablename__ = "monthly_totals"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    category = db.relationship("Category")

    __table_args__ = (db.UniqueConstraint("category_id", "year", "month"),)


class AuditLog(db.Model):
    """Every AI call, logged for explainability/transparency."""

    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime(timezone=True), default=now_utc)
    action = db.Column(db.String(50), nullable=False)  # parse | classify
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"))
    input_excerpt = db.Column(db.Text)
    output_summary = db.Column(db.Text)
