"""
Chooses and builds a Plotly chart from a structured request + executor result.

Deterministic. Never sees the raw user question, only the request dict.
"""

import plotly.express as px

TIME_KEYWORDS = ("date", "month", "year", "week", "time", "day")

HORIZONTAL_BAR_THRESHOLD = 8


def _is_time_like(column_name):
    """Cheap heuristic: does the column name suggest a time axis?"""
    name = column_name.lower()
    return any(kw in name for kw in TIME_KEYWORDS)


def visualize(request, outcome):
    """
    Returns {"status": "ok", "figure": fig, "chart_type": str, "reason": str}
    or {"status": "skipped", "reason": str} if no chart is appropriate.
    Assumes outcome["status"] == "ok".
    """
    if outcome.get("status") != "ok":
        return {"status": "skipped", "reason": "No result to visualize."}

    result_df = outcome["result"]
    value_col = outcome["value_col"]
    group_by = request["group_by"]
    agg = request.get("aggregation", "sum")
    metric = request.get("metric") or "rows"

    if result_df.empty:
        return {"status": "skipped", "reason": "The result is empty."}

    # ---------- Chart selection ----------
    if request.get("time_bucket") or _is_time_like(group_by):
        chart_type = "line"
        reason = (
            f"'{group_by}' is being viewed over time, so a line chart "
            f"shows the trend clearly."
        )
    elif len(result_df) > HORIZONTAL_BAR_THRESHOLD:
        chart_type = "horizontal_bar"
        reason = (
            f"There are {len(result_df)} categories — bars going sideways "
            f"keep the labels readable."
        )
    else:
        chart_type = "bar"
        reason = (
            f"'{group_by}' is categorical, so a bar chart makes the "
            f"comparison across groups easy to read."
        )

    # ---------- Build the figure ----------
    y_label = f"{agg} of {metric}" if metric != "rows" else "row count"

    if chart_type == "line":
        fig = px.line(
            result_df,
            x=group_by,
            y=value_col,
            markers=True,
            labels={group_by: group_by, value_col: y_label},
        )
    elif chart_type == "horizontal_bar":
        fig = px.bar(
            result_df,
            x=value_col,
            y=group_by,
            orientation="h",
            labels={group_by: group_by, value_col: y_label},
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
    else:
        fig = px.bar(
            result_df,
            x=group_by,
            y=value_col,
            labels={group_by: group_by, value_col: y_label},
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=400,
        showlegend=False,
    )

    return {
        "status": "ok",
        "figure": fig,
        "chart_type": chart_type,
        "reason": reason,
    }