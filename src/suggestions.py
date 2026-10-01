"""
Generates example questions based on the dataset's schema.
Deterministic — same schema gives same suggestions.
"""


def suggest(df, profile_result, max_suggestions=6):
    numeric = profile_result["numeric"]
    categorical = profile_result["categorical"]
    datetime_cols = profile_result["datetime"]

    suggestions = []

    # 1. Time trend (highest priority — most useful)
    if datetime_cols and numeric:
        suggestions.append(f"Show {numeric[0]} by month")

    # 2. Top-N per categorical column
    for cat in categorical[:2]:  # cap at 2 categories
        if numeric:
            suggestions.append(f"Top 5 {cat} by {numeric[0]}")

    # 3. Group-by pattern across remaining combinations
    for cat in categorical[:2]:
        for metric in numeric[:2]:
            q = f"Average {metric} by {cat}"
            if q not in suggestions:
                suggestions.append(q)

    # 4. Count pattern (works even without numeric columns)
    if categorical:
        suggestions.append(f"How many rows per {categorical[0]}")

    return suggestions[:max_suggestions]