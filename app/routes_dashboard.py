from flask import Blueprint, render_template

from .forecasting import project_next_month
from .models import Category, Document, LineItem, MonthlyTotal, db

bp = Blueprint("dashboard", __name__, url_prefix="")

TREND_CATEGORY_LIMIT = 4


@bp.route("/", methods=["GET"])
def index():
    spend_rows = (
        db.session.query(Category.name, db.func.sum(LineItem.amount))
        .join(LineItem, LineItem.category_id == Category.id)
        .group_by(Category.name)
        .order_by(db.func.sum(LineItem.amount).desc())
        .all()
    )
    spend_by_category = [{"category": name, "total": float(total or 0)} for name, total in spend_rows]

    kpis = _compute_kpis(spend_by_category)

    forecasts = []
    for category in Category.query.all():
        history = (
            MonthlyTotal.query
            .filter_by(category_id=category.id)
            .order_by(MonthlyTotal.year, MonthlyTotal.month)
            .all()
        )
        if not history:
            continue
        series = [(row.year, row.month, float(row.total_amount)) for row in history]
        projection = project_next_month(series)
        if projection is not None:
            forecasts.append({"category": category.name, "projected_next_month": projection})

    monthly_trend = _monthly_trend(top_categories=[row["category"] for row in spend_by_category[:TREND_CATEGORY_LIMIT]])

    return render_template(
        "dashboard.html",
        kpis=kpis,
        spend_by_category=spend_by_category,
        forecasts=forecasts,
        monthly_trend=monthly_trend,
    )


def _compute_kpis(spend_by_category):
    total_spend = sum(row["total"] for row in spend_by_category)
    doc_count = Document.query.count()
    category_count = len(spend_by_category)

    confidences = [c for (c,) in db.session.query(LineItem.confidence).filter(LineItem.confidence.isnot(None)).all()]
    avg_confidence = sum(confidences) / len(confidences) if confidences else None

    return {
        "total_spend": total_spend,
        "doc_count": doc_count,
        "category_count": category_count,
        "avg_confidence": avg_confidence,
    }


def _monthly_trend(top_categories):
    if not top_categories:
        return {"labels": [], "series": []}

    categories = Category.query.filter(Category.name.in_(top_categories)).all()
    rows_by_category = {}
    all_periods = set()

    for category in categories:
        rows = (
            MonthlyTotal.query
            .filter_by(category_id=category.id)
            .order_by(MonthlyTotal.year, MonthlyTotal.month)
            .all()
        )
        rows_by_category[category.name] = {(r.year, r.month): float(r.total_amount) for r in rows}
        all_periods.update(rows_by_category[category.name].keys())

    sorted_periods = sorted(all_periods)
    labels = [f"{y}-{m:02d}" for y, m in sorted_periods]

    series = []
    # preserve the original top_categories order (by total spend) rather than dict order
    for name in top_categories:
        values = rows_by_category.get(name, {})
        series.append({
            "category": name,
            "data": [values.get(period, 0) for period in sorted_periods],
        })

    return {"labels": labels, "series": series}
