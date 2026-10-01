"""
Turns a natural-language question into a structured request dict.

"""

import re

# Map user phrasing → canonical aggregation name.
# Order matters: more specific phrases first.
AGGREGATION_KEYWORDS = [
    ("average", "mean"),
    ("avg", "mean"),
    ("mean", "mean"),
    ("median", "median"),
    ("total", "sum"),
    ("sum", "sum"),
    ("highest", "sum"),
    ("lowest", "sum"),
    ("most", "sum"),
    ("least", "sum"),
    ("maximum", "max"),
    ("minimum", "min"),
    ("count", "count"),
    ("number of", "count"),
    ("how many", "count"),
]


def _find_column_by_name(name, columns):
    """Case-insensitive exact match of a column name."""
    name = name.lower()
    for col in columns:
        if col.lower() == name:
            return col
    return None


def _find_first_mentioned_column(text, columns):
    """Return the first column whose name appears anywhere in `text`."""
    text = text.lower()
    for col in columns:
        if col.lower() in text:
            return col
    return None


def interpret(question, df):
    """
    Returns {"status": "ok", "request": {...}} or
            {"status": "error", "message": "..."}.
    """
    q = question.lower().strip()
    if not q:
        return {"status": "error", "message": "Please enter a question."}

    all_cols = list(df.columns)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    categorical_cols = [c for c in all_cols if c not in numeric_cols]

    # --- 1. Aggregation ---
    aggregation = "sum"  # default for questions that don't specify one
    for keyword, agg in AGGREGATION_KEYWORDS:
        if keyword in q:
            aggregation = agg
            break

    # --- 2. Limit (top N / highest / most) ---
    limit = None
    m = re.search(r"\btop\s+(\d+)\b", q)
    if m:
        limit = int(m.group(1))
    elif any(w in q for w in ("highest", "most", "best", "top", "maximum")):
        limit = 1

    # --- 3. Look for "by <col>" to lock in either metric or group_by ---
    metric = None
    group_by = None
    m = re.search(r"\bby\s+([a-zA-Z_][a-zA-Z0-9_]*)\b", q)
    if m:
        matched = _find_column_by_name(m.group(1), all_cols)
        if matched:
            if matched in numeric_cols:
                metric = matched
            else:
                group_by = matched

    # --- 4. Fill in missing metric / group_by from mentioned columns ---
    if metric is None:
        metric = _find_first_mentioned_column(q, numeric_cols)

    if group_by is None:
        group_by = _find_first_mentioned_column(q, categorical_cols)

    # --- 5. Validation before returning ---
    if group_by is None:
        # Try to name the specific word the user asked to group by
        m = re.search(r"\bby\s+([a-zA-Z_][a-zA-Z0-9_]*)\b", q)
        if m:
            requested = m.group(1)
            message = (
                f"There's no column called '{requested}' in this dataset. "
                f"Available columns: {', '.join(all_cols)}."
            )
        else:
            message = (
                "I couldn't figure out which column to group by. "
                f"Available columns: {', '.join(all_cols)}."
            )
        return {"status": "error", "message": message}
    
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

    return {
        "status": "ok",
        "request": {
            "operation": "groupby_aggregate",
            "group_by": group_by,
            "metric": metric,
            "aggregation": aggregation,
            "sort": "desc" if limit is not None else None,
            "limit": limit,
        },
    }