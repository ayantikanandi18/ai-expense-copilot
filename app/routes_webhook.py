"""Headless ingestion endpoint — the shape an n8n 'HTTP Request' node or a
Zapier 'Webhooks by Zapier' action would call after picking up a new email
attachment / Google Sheets row / Drive file. See README for wiring examples.
"""

from flask import Blueprint, jsonify, request

from .models import db
from .pipeline import process_text

bp = Blueprint("webhook", __name__, url_prefix="/webhooks")


@bp.route("/ingest", methods=["POST"])
def ingest():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "expected JSON body with a 'text' field"}), 400

    try:
        document = process_text(text, source="webhook")
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500

    return jsonify({
        "ok": True,
        "document_id": document.id,
        "vendor": document.vendor,
        "total_amount": float(document.total_amount) if document.total_amount else None,
        "line_items": len(document.line_items),
    })
