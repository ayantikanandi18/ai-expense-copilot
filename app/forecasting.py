"""Simple linear-trend forecast over monthly category totals.

Deliberately not a heavyweight time-series library (no statsmodels/prophet):
with only a handful of months of real data, a plain least-squares trend line
is honest about its own simplicity and easy to explain in an interview.
"""


def project_next_month(monthly_totals):
    """monthly_totals: list of (year, month, amount) sorted chronologically.

    Returns the projected next-month amount via ordinary least-squares over
    the sequence index, or None if there isn't enough history (<2 points).
    """
    n = len(monthly_totals)
    if n < 2:
        return None

    xs = list(range(n))
    ys = [float(amount) for _, _, amount in monthly_totals]

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)

    if denominator == 0:
        return round(mean_y, 2)

    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    next_x = n  # the next point in the sequence
    projection = intercept + slope * next_x
    return round(max(projection, 0), 2)
