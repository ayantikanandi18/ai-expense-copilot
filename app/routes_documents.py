import io

from flask import Blueprint, flash, redirect, render_template, request, url_for
from pypdf import PdfReader

from .models import Document, db
from .pipeline import process_text

bp = Blueprint("documents", __name__, url_prefix="/documents")


@bp.route("/", methods=["GET"])
def list_documents():
    documents = Document.query.order_by(Document.created_at.desc()).all()
    return render_template("documents.html", documents=documents)


@bp.route("/upload", methods=["POST"])
def upload():
    pasted_text = (request.form.get("raw_text") or "").strip()
    file = request.files.get("file")

    text = pasted_text
    if not text and file and file.filename:
        if file.filename.lower().endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file.read()))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            text = file.read().decode("utf-8", errors="replace")

    if not text.strip():
        flash("Paste some text or choose a .txt/.pdf file first.", "error")
        return redirect(url_for("dashboard.index"))

    try:
        document = process_text(text, source="upload")
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        flash(f"Processing failed: {exc}", "error")
        return redirect(url_for("dashboard.index"))

    flash(f"Processed: {document.vendor or 'document'} #{document.id}", "success")
    return redirect(url_for("documents.detail", document_id=document.id))


@bp.route("/<int:document_id>", methods=["GET"])
def detail(document_id):
    document = Document.query.get_or_404(document_id)
    return render_template("document_detail.html", document=document)


@bp.route("/<int:document_id>/delete", methods=["POST"])
def delete(document_id):
    document = Document.query.get_or_404(document_id)
    db.session.delete(document)
    db.session.commit()
    flash("Document deleted.", "success")
    return redirect(url_for("documents.list_documents"))
