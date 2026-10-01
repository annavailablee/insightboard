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
        warm_sequence = ["#7E0B0B", "#6E1C1C", "#6E2A2A", "#E9C9B7", "#8B3A3A"]
        fig.update_layout(yaxis=dict(autorange="reversed"))
    else:
        fig = px.bar(
            result_df,
            x=group_by,
            y=value_col,
            labels={group_by: group_by, value_col: y_label},
        )
    sage_sequence = ["#6D765B", "#6D765B", "#A3B2A1", "#314128", "#B2C2B2"]

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=380,
        showlegend=False,
        colorway=sage_sequence,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, -apple-system, sans-serif",
                  size=13, color="#314128"),
        xaxis=dict(gridcolor="#B2C2B2", linecolor="#A3B2A1",
                   zerolinecolor="#A3B2A1"),
        yaxis=dict(gridcolor="#B2C2B2", linecolor="#A3B2A1",
                   zerolinecolor="#A3B2A1"),
    )
    fig.update_traces(marker_line_width=0)


    return {
        "status": "ok",
        "figure": fig,
        "chart_type": chart_type,
        "reason": reason,
    }