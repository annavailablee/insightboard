"""
Turns a natural-language question into a structured request dict.
Rule-based MVP. Will later be swapped for an LLM returning the same shape.
"""

import re
from src.schema import profile

AGGREGATION_KEYWORDS = [
    ("average", "mean"), ("avg", "mean"), ("mean", "mean"),
    ("median", "median"),
    ("total", "sum"), ("sum", "sum"),
    ("highest", "sum"), ("lowest", "sum"),
    ("most", "sum"), ("least", "sum"),
    ("maximum", "max"), ("minimum", "min"),
    ("count", "count"), ("number of", "count"), ("how many", "count"),
]

# Natural word -> bucket code used by pandas .dt.to_period()
TIME_BUCKET_KEYWORDS = {
    "monthly": "month", "by month": "month", "per month": "month",
    "month": "month",
    "yearly": "year", "annual": "year", "annually": "year",
    "by year": "year", "per year": "year", "year": "year",
    "quarterly": "quarter", "by quarter": "quarter", "quarter": "quarter",
    "weekly": "week", "by week": "week", "week": "week",
    "daily": "day", "by day": "day", "day": "day",
}


def _find_column_by_name(name, columns):
    name = name.lower()
    for col in columns:
        if col.lower() == name:
            return col
    return None


def _find_first_mentioned_column(text, columns):
    text = text.lower()
    for col in columns:
        if col.lower() in text:
            return col
    return None


def _detect_time_bucket(q):
    """Return the bucket name ('month', 'year', ...) or None.
    Prefers multi-word matches so 'by month' beats a stray 'month'."""
    for phrase in sorted(TIME_BUCKET_KEYWORDS, key=len, reverse=True):
        if phrase in q:
            return TIME_BUCKET_KEYWORDS[phrase]
    return None


def interpret(question, df):
    q = question.lower().strip()
    if not q:
        return {"status": "error", "message": "Please enter a question."}

    prof = profile(df)
    all_cols = list(df.columns)
    numeric_cols = prof["numeric"]
    datetime_cols = prof["datetime"]
    categorical_cols = prof["categorical"]

    # --- 1. Aggregation ---
    aggregation = "sum"
    for keyword, agg in AGGREGATION_KEYWORDS:
        if keyword in q:
            aggregation = agg
            break

    # --- 2. Limit ---
    limit = None
    m = re.search(r"\btop\s+(\d+)\b", q)
    if m:
        limit = int(m.group(1))
    elif any(w in q for w in ("highest", "most", "best", "top", "maximum")):
        limit = 1

    # --- 3. Time bucket? ---
    time_bucket = _detect_time_bucket(q)

    # --- 4. Metric: numeric column named after "by" or mentioned anywhere ---
    metric = None
    m = re.search(r"\bby\s+([a-zA-Z_][a-zA-Z0-9_]*)\b", q)
    if m:
        matched = _find_column_by_name(m.group(1), all_cols)
        if matched in numeric_cols:
            metric = matched

    if metric is None:
        metric = _find_first_mentioned_column(q, numeric_cols)

    # --- 5. Group-by ---
    # Order of preference:
    #   a) explicit "by <name>" that matches a categorical column
    #   b) if a time bucket was requested, use a datetime column
    #   c) any categorical column mentioned by name
    group_by = None
    if m:
        matched = _find_column_by_name(m.group(1), all_cols)
        if matched in categorical_cols:
            group_by = matched

    if group_by is None and time_bucket is not None and datetime_cols:
        group_by = datetime_cols[0]

    if group_by is None:
        group_by = _find_first_mentioned_column(q, categorical_cols)

    # --- 6. Validation ---
    if group_by is None:
        if m:
            return {
                "status": "error",
                "message": (
                    f"There's no column called '{m.group(1)}' in this dataset. "
                    f"Available columns: {', '.join(all_cols)}."
                ),
            }
        return {
            "status": "error",
            "message": (
                "I couldn't figure out which column to group by. "
                f"Available columns: {', '.join(all_cols)}."
            ),
        }

    if time_bucket is not None and group_by not in datetime_cols:
        return {
            "status": "error",
            "message": (
                f"I can't bucket by {time_bucket} because '{group_by}' "
                f"isn't a date column."
            ),
        }

    if aggregation != "count" and metric is None:
        return {
            "status": "error",
            "message": (
                "I couldn't find a numeric column to aggregate. "
                f"Numeric columns: {', '.join(numeric_cols) or 'none'}."
            ),
        }

    if metric is not None and metric == group_by:
        return {
            "status": "error",
            "message": "The metric and grouping column can't be the same.",
        }

    request = {
        "operation": "groupby_aggregate",
        "group_by": group_by,
        "metric": metric,
        "aggregation": aggregation,
        "sort": "desc" if limit is not None else None,
        "limit": limit,
    }
    if time_bucket is not None:
        request["time_bucket"] = time_bucket
    return {"status": "ok", "request": request}