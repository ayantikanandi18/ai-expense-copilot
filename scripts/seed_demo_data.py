"""Seeds clearly-synthetic demo data so the dashboard has something to show on
a first run, instead of being blank. Every row is fabricated for local
demo/screenshot purposes — this is NOT sample output from the Groq pipeline,
and the raw_text on each document says so explicitly.

Run: python scripts/seed_demo_data.py
Re-running it wipes and re-seeds (safe to run repeatedly).
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import AuditLog, Category, Document, LineItem, MonthlyTotal, db

# (year, month, day, vendor, category, amount, confidence, rationale, source)
DEMO_DOCS = [
    (2026, 3, 3, "AWS Cloud Services", "Software & Subscriptions", 320.00, 0.96,
     "Recurring cloud infrastructure subscription billing.", "upload"),
    (2026, 3, 5, "United Airlines", "Travel", 600.00, 0.88,
     "Airfare line item matches travel category keywords.", "upload"),
    (2026, 3, 9, "Blue Bottle Coffee", "Meals & Entertainment", 210.00, 0.83,
     "Coffee/food vendor consistent with meals category.", "webhook"),
    (2026, 3, 12, "Office Depot", "Office Supplies", 90.00, 0.91,
     "Retailer and item description match office supplies.", "upload"),
    (2026, 3, 15, "Meta Ads", "Marketing & Advertising", 500.00, 0.94,
     "Ad platform billing matches marketing & advertising.", "upload"),
    (2026, 3, 20, "Deloitte Consulting", "Professional Services", 1200.00, 0.92,
     "Consulting firm invoice matches professional services.", "upload"),

    (2026, 4, 3, "AWS Cloud Services", "Software & Subscriptions", 340.00, 0.96,
     "Recurring cloud infrastructure subscription billing.", "upload"),
    (2026, 4, 6, "Delta Airlines", "Travel", 750.00, 0.87,
     "Airfare line item matches travel category keywords.", "webhook"),
    (2026, 4, 10, "Panera Bread", "Meals & Entertainment", 240.00, 0.81,
     "Restaurant vendor consistent with meals category.", "upload"),
    (2026, 4, 13, "Staples", "Office Supplies", 85.00, 0.90,
     "Retailer and item description match office supplies.", "upload"),
    (2026, 4, 16, "Meta Ads", "Marketing & Advertising", 650.00, 0.95,
     "Ad platform billing matches marketing & advertising.", "upload"),
    (2026, 4, 21, "Deloitte Consulting", "Professional Services", 1200.00, 0.92,
     "Consulting firm invoice matches professional services.", "upload"),

    (2026, 5, 4, "AWS Cloud Services", "Software & Subscriptions", 365.00, 0.97,
     "Recurring cloud infrastructure subscription billing.", "upload"),
    (2026, 5, 7, "United Airlines", "Travel", 700.00, 0.89,
     "Airfare line item matches travel category keywords.", "upload"),
    (2026, 5, 11, "Sweetgreen", "Meals & Entertainment", 265.00, 0.82,
     "Restaurant vendor consistent with meals category.", "webhook"),
    (2026, 5, 14, "Office Depot", "Office Supplies", 100.00, 0.91,
     "Retailer and item description match office supplies.", "upload"),
    (2026, 5, 17, "Google Ads", "Marketing & Advertising", 720.00, 0.95,
     "Ad platform billing matches marketing & advertising.", "upload"),
    (2026, 5, 22, "Deloitte Consulting", "Professional Services", 1500.00, 0.93,
     "Consulting firm invoice matches professional services.", "upload"),

    (2026, 6, 3, "AWS Cloud Services", "Software & Subscriptions", 390.00, 0.97,
     "Recurring cloud infrastructure subscription billing.", "upload"),
    (2026, 6, 8, "Delta Airlines", "Travel", 900.00, 0.88,
     "Airfare line item matches travel category keywords.", "upload"),
    (2026, 6, 12, "Blue Bottle Coffee", "Meals & Entertainment", 300.00, 0.84,
     "Coffee/food vendor consistent with meals category.", "webhook"),
    (2026, 6, 15, "Staples", "Office Supplies", 95.00, 0.90,
     "Retailer and item description match office supplies.", "upload"),
    (2026, 6, 18, "Google Ads", "Marketing & Advertising", 800.00, 0.96,
     "Ad platform billing matches marketing & advertising.", "upload"),
    (2026, 6, 24, "Deloitte Consulting", "Professional Services", 1600.00, 0.93,
     "Consulting firm invoice matches professional services.", "upload"),
]


def seed():
    app = create_app()
    with app.app_context():
        LineItem.query.delete()
        Document.query.delete()
        MonthlyTotal.query.delete()
        AuditLog.query.delete()
        db.session.commit()

        categories = {c.name: c for c in Category.query.all()}

        for year, month, day, vendor, cat_name, amount, confidence, rationale, source in DEMO_DOCS:
            category = categories[cat_name]

            document = Document(
                source=source,
                vendor=vendor,
                document_date=date(year, month, day),
                total_amount=amount,
                raw_text=(
                    f"[SYNTHETIC DEMO DATA — not real]\n{vendor}\n"
                    f"Date: {year}-{month:02d}-{day:02d}\nAmount: ${amount:.2f}"
                ),
                redacted=False,
            )
            db.session.add(document)
            db.session.flush()

            db.session.add(LineItem(
                document_id=document.id,
                description=f"{vendor} — {cat_name}",
                amount=amount,
                category=category,
                confidence=confidence,
                rationale=rationale,
            ))

            db.session.add(AuditLog(
                action="classify",
                document_id=document.id,
                input_excerpt=f"{vendor} — {cat_name}",
                output_summary=f'{{"category": "{cat_name}", "confidence": {confidence}, "rationale": "{rationale}"}}',
            ))

            row = MonthlyTotal.query.filter_by(category_id=category.id, year=year, month=month).first()
            if row:
                row.total_amount = float(row.total_amount) + amount
            else:
                db.session.add(MonthlyTotal(category_id=category.id, year=year, month=month, total_amount=amount))

        db.session.commit()
        months = len({(y, m) for y, m, *_ in DEMO_DOCS})
        print(f"Seeded {len(DEMO_DOCS)} synthetic documents across {months} months.")


if __name__ == "__main__":
    seed()
