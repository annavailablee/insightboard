"""
Executes a validated structured request against a DataFrame.

This module is deliberately dumb. It never sees the raw question. It only
accepts the exact schema produced by interpreter.interpret().
"""

import pandas as pd

SUPPORTED_AGGREGATIONS = {"sum", "mean", "count", "min", "max", "median"}
SUPPORTED_OPERATIONS = {"groupby_aggregate"}


def execute(request, df):
    """
    Returns {"status": "ok", "result": <DataFrame>, "value_col": str} or
            {"status": "error", "message": "..."}.
    """
    operation = request.get("operation")
    if operation not in SUPPORTED_OPERATIONS:
        return {
            "status": "error",
            "message": f"Unsupported operation: {operation!r}.",
        }

    group_by = request.get("group_by")
    metric = request.get("metric")
    aggregation = request.get("aggregation", "sum")
    sort = request.get("sort")
    limit = request.get("limit")

    # --- Validate against the DataFrame ---
    if group_by not in df.columns:
        return {"status": "error", "message": f"Column {group_by!r} not found."}

    if aggregation not in SUPPORTED_AGGREGATIONS:
        return {
            "status": "error",
            "message": f"Unsupported aggregation: {aggregation!r}.",
        }

    if aggregation != "count":
        if metric is None:
            return {"status": "error", "message": "No metric column provided."}
        if metric not in df.columns:
            return {"status": "error", "message": f"Column {metric!r} not found."}
        if not pd.api.types.is_numeric_dtype(df[metric]):
            return {
                "status": "error",
                "message": f"Column {metric!r} is not numeric and can't be aggregated.",
            }

    # --- Perform the operation ---
    if aggregation == "count" or metric is None:
        result = df.groupby(group_by, dropna=False).size().reset_index(name="count")
        value_col = "count"
    else:
        result = (
            df.groupby(group_by, dropna=False)[metric]
            .agg(aggregation)
            .reset_index()
        )
        value_col = metric

    # --- Sort ---
    if sort == "desc":
        result = result.sort_values(value_col, ascending=False)
    elif sort == "asc":
        result = result.sort_values(value_col, ascending=True)

    # --- Limit ---
    if limit is not None:
        result = result.head(int(limit))

    return {
        "status": "ok",
        "result": result.reset_index(drop=True),
        "value_col": value_col,
    }