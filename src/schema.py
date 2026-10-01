"""
Classifies each column in a DataFrame as one of:
numeric / categorical / datetime / id / text / boolean.

Used by the interpreter to reason about what questions are answerable,
and by the visualizer to pick appropriate charts.
"""

import pandas as pd

DATETIME_PARSE_THRESHOLD = 0.8   # fraction of non-null values that must parse
ID_MIN_ROWS = 20                 # don't call something "id" on tiny datasets
CATEGORICAL_MAX_UNIQUE = 20


def _datetime_coverage(series):
    """Return fraction of non-null values parseable as dates, or None."""
    if pd.api.types.is_numeric_dtype(series):
        return None
    non_null = series.dropna()
    if non_null.empty:
        return None
    parsed = pd.to_datetime(non_null, errors="coerce")
    return float(parsed.notna().mean())


def profile(df):
    """
    Returns {
        "columns": {col: {"kind": str, "dtype": str, ...}},
        "numeric": [...], "categorical": [...], "datetime": [...],
        "id": [...], "text": [...], "boolean": [...],
    }
    """
    columns = {}
    buckets = {k: [] for k in
               ("numeric", "categorical", "datetime", "id", "text", "boolean")}
    n_rows = len(df)

    for col in df.columns:
        s = df[col]
        meta = {"dtype": str(s.dtype)}

        if pd.api.types.is_bool_dtype(s):
            kind = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(s):
            kind = "datetime"
        elif pd.api.types.is_numeric_dtype(s):
            kind = "numeric"
        else:
            coverage = _datetime_coverage(s)
            if coverage is not None and coverage >= DATETIME_PARSE_THRESHOLD:
                kind = "datetime"
                meta["parse_coverage"] = round(coverage, 3)
            else:
                n_unique = int(s.nunique(dropna=True))
                meta["n_unique"] = n_unique
                if n_rows >= ID_MIN_ROWS and n_unique == n_rows:
                    kind = "id"
                elif (
                    n_unique <= CATEGORICAL_MAX_UNIQUE
                    or (n_rows > 0 and n_unique / n_rows < 0.5)
                ):
                    kind = "categorical"
                else:
                    kind = "text"

        meta["kind"] = kind
        columns[col] = meta
        buckets[kind].append(col)

    return {"columns": columns, **buckets}