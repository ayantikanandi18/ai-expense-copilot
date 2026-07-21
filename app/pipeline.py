"""Shared parse -> classify -> store pipeline used by both the upload route
and the webhook route, so the two entry points can't drift apart."""

from datetime import datetime

from .ai import llm_client
from .ai.privacy import redact
from .models import AuditLog, Category, Document, LineItem, MonthlyTotal, db


def process_text(raw_text, source="upload"):
    redacted_text, was_redacted = redact(raw_text)

    parsed = llm_client.parse_document(redacted_text)
    db.session.add(AuditLog(
        action="parse",
        input_excerpt=redacted_text[:500],
        output_summary=str(parsed)[:1000],
    ))

    doc_date = None
    if parsed.get("document_date"):
        try:
            doc_date = datetime.strptime(parsed["document_date"], "%Y-%m-%d").date()
        except ValueError:
            doc_date = None

    document = Document(
        source=source,
        vendor=parsed.get("vendor"),
        document_date=doc_date,
        total_amount=parsed.get("total_amount"),
        raw_text=redacted_text,
        redacted=was_redacted,
    )
    db.session.add(document)
    db.session.flush()  # assign document.id

    categories = [c.name for c in Category.query.all()]

    for item in parsed.get("line_items", []):
        description = item.get("description") or ""
        amount = item.get("amount")
        classification = llm_client.classify_line_item(description, categories)

        db.session.add(AuditLog(
            action="classify",
            document_id=document.id,
            input_excerpt=description[:500],
            output_summary=str(classification)[:1000],
        ))

        category = Category.query.filter_by(name=classification.get("category")).first()
        if not category:
            category = Category.query.filter_by(name="Uncategorized").first()

        line_item = LineItem(
            document_id=document.id,
            description=description,
            amount=amount,
            category=category,
            confidence=classification.get("confidence"),
            rationale=classification.get("rationale"),
        )
        db.session.add(line_item)

        if amount and category and doc_date:
            _accumulate_monthly_total(category.id, doc_date.year, doc_date.month, float(amount))

    db.session.commit()
    return document


def _accumulate_monthly_total(category_id, year, month, amount):
    row = MonthlyTotal.query.filter_by(category_id=category_id, year=year, month=month).first()
    if row:
        row.total_amount = float(row.total_amount) + amount
    else:
        row = MonthlyTotal(category_id=category_id, year=year, month=month, total_amount=amount)
        db.session.add(row)
