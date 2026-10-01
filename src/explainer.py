"""
Turns (structured_request, executor_outcome) into a plain-English Result
and Why. Deterministic. Never looks at the original user question.
"""

import html

def _format_number(value):
    """Human-friendly number formatting."""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)

    if abs(v) >= 1_000_000:
        return f"{v:,.2f}".rstrip("0").rstrip(".")
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if v.is_integer():
        return f"{int(v):,}"
    return f"{v:,.2f}".rstrip("0").rstrip(".")


AGG_PHRASES = {
    "sum": "total",
    "mean": "average",
    "median": "median",
    "count": "row count",
    "min": "minimum",
    "max": "maximum",
}


def explain(request, outcome):
    """
    Returns {"result": str, "why": str}.
    Assumes outcome["status"] == "ok" — callers should check first.
    """
    if outcome.get("status") != "ok":
        return {"result": "", "why": ""}

    result_df = outcome["result"]
    value_col = outcome["value_col"]
    group_by = request["group_by"]
    metric = request.get("metric")
    agg = request.get("aggregation", "sum")
    limit = request.get("limit")

    if result_df.empty:
        return {
            "result": f"No rows matched — nothing to report for {group_by}.",
            "why": "The grouping column contained no values to aggregate.",
        }

    agg_phrase = AGG_PHRASES.get(agg, agg)

    # ---------- Why ----------
    if agg == "count":
        why = (
            f"Rows were grouped by <strong>{group_by}</strong> and counted. "
            f"The result shows how many rows fall into each group."
        )
    else:
        why = (
            f"<strong>{metric}</strong> was aggregated by "
            f"<strong>{agg_phrase}</strong> for each unique "
            f"value of <strong>{group_by}</strong>. The result shows one row per group."
        )

    # ---------- Result ----------
    top_row = result_df.iloc[0]
    top_group = top_row[group_by]
    top_value = top_row[value_col]

    if limit == 1:
        # Detect ties at the top value
        ties = result_df[result_df[value_col] == top_value][group_by].tolist()

        if len(ties) > 1:
            joined = ", ".join(str(t) for t in ties[:-1]) + f" and {ties[-1]}"
            result = (
                f"<strong>{html.escape(str(top_group))}</strong> tied for the highest {agg_phrase} "
                f"{metric or 'count'} at {_format_number(top_value)}."
            )
        else:
            result = (
                f"<strong>{html.escape(str(top_group))}</strong> had the highest {agg_phrase} "
                f"{metric or 'count'} at {_format_number(top_value)}."
            )

    elif limit is not None and limit > 1:
        result = (
            f"Top {limit} values of {group_by} by {agg_phrase} "
            f"{metric or 'count'}: <strong>{html.escape(str(top_group))}</strong> leads "
            f"at {_format_number(top_value)}."
        )

    else:
        # Full breakdown
        result = (
            f"Breakdown of {agg_phrase} {metric or 'count'} by {group_by} "
            f"across {len(result_df)} group(s). "
            f"Highest: <strong>{html.escape(str(top_group))}</strong> at "
            f"{_format_number(top_value)}."
        )

    return {"result": result, "why": why}