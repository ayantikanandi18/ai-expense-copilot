from flask import Blueprint, render_template

from .forecasting import project_next_month
from .models import Category, LineItem, MonthlyTotal, db

bp = Blueprint("dashboard", __name__, url_prefix="")


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

    return render_template(
        "dashboard.html",
        spend_by_category=spend_by_category,
        forecasts=forecasts,
    )
