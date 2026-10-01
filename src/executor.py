import pandas as pd

SUPPORTED_AGGREGATIONS = {"sum", "mean", "count", "min", "max", "median"}
SUPPORTED_OPERATIONS = {"groupby_aggregate"}

TIME_BUCKET_TO_PERIOD = {
    "day": "D", "week": "W", "month": "M", "quarter": "Q", "year": "Y",
}


def execute(request, df):
    operation = request.get("operation")
    if operation not in SUPPORTED_OPERATIONS:
        return {"status": "error",
                "message": f"Unsupported operation: {operation!r}."}

    group_by = request.get("group_by")
    metric = request.get("metric")
    aggregation = request.get("aggregation", "sum")
    sort = request.get("sort")
    limit = request.get("limit")
    time_bucket = request.get("time_bucket")

    # --- Validate ---
    if group_by not in df.columns:
        return {"status": "error", "message": f"Column {group_by!r} not found."}

    if aggregation not in SUPPORTED_AGGREGATIONS:
        return {"status": "error",
                "message": f"Unsupported aggregation: {aggregation!r}."}

    if aggregation != "count":
        if metric is None:
            return {"status": "error", "message": "No metric column provided."}
        if metric not in df.columns:
            return {"status": "error",
                    "message": f"Column {metric!r} not found."}
        if not pd.api.types.is_numeric_dtype(df[metric]):
            return {"status": "error",
                    "message": f"Column {metric!r} is not numeric."}

    if time_bucket is not None and time_bucket not in TIME_BUCKET_TO_PERIOD:
        return {"status": "error",
                "message": f"Unsupported time bucket: {time_bucket!r}."}

    # --- Derive time bucket if requested ---
    effective_group = group_by
    if time_bucket is not None:
        parsed = pd.to_datetime(df[group_by], errors="coerce")
        if parsed.notna().mean() < 0.5:
            return {"status": "error",
                    "message": (f"Column {group_by!r} can't be interpreted "
                                f"as dates for bucketing.")}
        df = df.copy()
        df["_bucket"] = (
            parsed.dt.to_period(TIME_BUCKET_TO_PERIOD[time_bucket]).astype(str)
        )
        effective_group = "_bucket"

    # --- Aggregate ---
    if aggregation == "count" or metric is None:
        result = df.groupby(effective_group, dropna=False).size().reset_index(name="count")
        value_col = "count"
    else:
        result = (df.groupby(effective_group, dropna=False)[metric]
                    .agg(aggregation).reset_index())
        value_col = metric

    # --- Rename bucket back to original column name ---
    if time_bucket is not None:
        result = result.rename(columns={"_bucket": group_by})

    # --- Sort ---
    if sort == "desc":
        result = result.sort_values(value_col, ascending=False)
    elif sort == "asc":
        result = result.sort_values(value_col, ascending=True)
    elif time_bucket is not None:
        # No explicit sort + a time axis → chronological is the right default.
        result = result.sort_values(group_by, ascending=True)

    if limit is not None:
        result = result.head(int(limit))

    return {"status": "ok", "result": result.reset_index(drop=True),
            "value_col": value_col}