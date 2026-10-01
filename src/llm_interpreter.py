"""
LLM-based interpreter.

Contract: same signature and return shape as src.interpreter.interpret().
The caller (app.py) doesn't care which one it uses.
"""

import json
import time
from google import genai
from src.schema import profile

MODEL_NAME = "gemini-flash-latest"

SUPPORTED_AGGREGATIONS = ["sum", "mean", "median", "count", "min", "max"]
SUPPORTED_TIME_BUCKETS = ["day", "week", "month", "quarter", "year"]


SYSTEM_PROMPT = """You convert a user's natural-language question about a
tabular dataset into a single JSON object describing a group-by aggregation.

You will receive:
  1. A list of the dataset's columns with their kinds.
  2. A user question.

You must respond with ONLY a JSON object matching this schema:

{
  "operation": "groupby_aggregate",
  "group_by": "<column name>",
  "metric": "<column name>" | null,
  "aggregation": "sum" | "mean" | "median" | "count" | "min" | "max",
  "sort": "desc" | "asc" | null,
  "limit": <integer> | null,
  "time_bucket": "day" | "week" | "month" | "quarter" | "year" | null,
  "error": "<message>" | null
}

Rules:
- group_by MUST be one of the listed column names (case-sensitive).
- metric MUST be a numeric column, or null only if aggregation is "count".
- If the user asks "top N" or "highest"/"most"/"best", set sort="desc" and
  limit=N (or 1 if no N given).
- If the user asks "lowest"/"least"/"worst", set sort="asc" and limit=N
  (or 1 if no N given).
- If the user references a time period ("monthly", "by year", "quarterly"),
  set time_bucket to the right bucket AND set group_by to a datetime column.
- If the question cannot be answered with the available columns, set all
  other fields to null and put a short explanation in "error". Do NOT invent
  columns that aren't in the list.
- If the question is ambiguous but could be answered, make the most reasonable
  choice and explain in "error" is NOT used — just answer.
- Never include any text outside the JSON object.

Examples:

Columns: date (datetime), region (categorical), product (categorical),
         units (numeric), revenue (numeric)

Q: "Which region had the highest average revenue?"
A: {"operation":"groupby_aggregate","group_by":"region","metric":"revenue",
    "aggregation":"mean","sort":"desc","limit":1,"time_bucket":null,"error":null}

Q: "Top 5 products by revenue"
A: {"operation":"groupby_aggregate","group_by":"product","metric":"revenue",
    "aggregation":"sum","sort":"desc","limit":5,"time_bucket":null,"error":null}

Q: "Monthly revenue trend"
A: {"operation":"groupby_aggregate","group_by":"date","metric":"revenue",
    "aggregation":"sum","sort":null,"limit":null,"time_bucket":"month","error":null}

Q: "What is customer retention?"
A: {"operation":"groupby_aggregate","group_by":null,"metric":null,
    "aggregation":null,"sort":null,"limit":null,"time_bucket":null,
    "error":"This dataset has no customer identifier or date of first purchase, so retention cannot be computed."}
"""


def _column_context(df):
    """A compact, human-readable description of the columns — no data."""
    prof = profile(df)
    lines = []
    for col, meta in prof["columns"].items():
        lines.append(f"- {col} ({meta['kind']})")
    return "\n".join(lines)


def _build_prompt(df, question):
    return (
        f"Columns:\n{_column_context(df)}\n\n"
        f"User question: {question}"
    )


def _validate_request(request, df):
    """Same checks the rule-based interpreter applies. Returns None if OK,
    or an error-message string."""
    if request.get("error"):
        return request["error"]

    all_cols = list(df.columns)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    datetime_cols = list(df.select_dtypes(include="datetime").columns)

    group_by = request.get("group_by")
    metric = request.get("metric")
    agg = request.get("aggregation")
    bucket = request.get("time_bucket")

    if group_by not in all_cols:
        return f"The LLM chose a column that doesn't exist: {group_by!r}."

    if agg not in SUPPORTED_AGGREGATIONS:
        return f"Unsupported aggregation from LLM: {agg!r}."

    if agg != "count":
        if metric not in numeric_cols:
            return (
                f"LLM chose a metric that isn't numeric or doesn't exist: "
                f"{metric!r}."
            )

    if bucket is not None:
        if bucket not in SUPPORTED_TIME_BUCKETS:
            return f"Unsupported time bucket from LLM: {bucket!r}."
        # If a time bucket was requested, group_by must be datetime-like.
        if not any(group_by == c for c in datetime_cols):
            # The LLM might have picked an object column that parses as dates;
            # we let the executor decide. Don't hard-fail here.
            pass

    return None


def interpret(question, df, api_key):
    """
    Same contract as src.interpreter.interpret().
    """
    q = (question or "").strip()
    if not q:
        return {"status": "error", "message": "Please enter a question."}

    client = genai.Client(api_key=api_key)
    response = None
    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=_build_prompt(df, q),
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                },
            )
            break
        except Exception as e:
            last_error = e
            msg = str(e)
            # Retry only on transient server errors; fail fast on auth/model errors.
            transient = ("503" in msg or "UNAVAILABLE" in msg
                         or "500" in msg or "INTERNAL" in msg)
            if not transient or attempt == 2:
                return {
                    "status": "error",
                    "message": f"The LLM request failed: {e}",
                }
            time.sleep(2 ** attempt)  # 1s, then 2s

    if response is None:
        return {
            "status": "error",
            "message": f"The LLM request failed after 3 attempts: {last_error}",
        }

    raw = (response.text or "").strip()

    try:
        request = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "The LLM returned something that wasn't valid JSON.",
        }

    validation_error = _validate_request(request, df)
    if validation_error:
        return {"status": "error", "message": validation_error}

    # Normalize to the same key set the rest of the app expects.
    normalized = {
        "operation": "groupby_aggregate",
        "group_by": request["group_by"],
        "metric": request.get("metric"),
        "aggregation": request.get("aggregation"),
        "sort": request.get("sort"),
        "limit": request.get("limit"),
    }
    if request.get("time_bucket"):
        normalized["time_bucket"] = request["time_bucket"]

    return {"status": "ok", "request": normalized}