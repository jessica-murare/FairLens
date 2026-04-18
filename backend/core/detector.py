import pandas as pd

PROTECTED_KEYWORDS = {
    "gender":    ["gender", "sex", "male", "female"],
    "race":      ["race", "ethnicity", "ethnic", "nationality"],
    "age":       ["age", "dob", "birthdate", "birth_year"],
    "religion":  ["religion", "faith", "belief"],
    "disability":["disability", "disabled", "impairment"],
}

TARGET_KEYWORDS = [
    "label", "target", "outcome", "result", "decision",
    "hired", "approved", "granted", "score", "class"
]

def detect_columns(df: pd.DataFrame) -> dict:
    protected = {}
    target = None
    col_lower = {col: col.lower() for col in df.columns}

    # Detect protected attributes
    for col, col_l in col_lower.items():
        for category, keywords in PROTECTED_KEYWORDS.items():
            if any(kw in col_l for kw in keywords):
                protected[col] = category
                break

    # Detect target column
    for col, col_l in col_lower.items():
        if any(kw in col_l for kw in TARGET_KEYWORDS):
            target = col
            break

    # Fallback: last binary column as target if nothing found
    if not target:
        for col in reversed(df.columns):
            if df[col].nunique() == 2:
                target = col
                break

    # Detect feature columns (everything else)
    feature_cols = [
        c for c in df.columns
        if c not in protected and c != target
    ]

    return {
        "protected_attributes": protected,
        "target_column": target,
        "feature_columns": feature_cols,
        "confidence": _confidence_score(protected, target)
    }

def _confidence_score(protected: dict, target: str) -> str:
    if protected and target:
        return "high"
    elif protected or target:
        return "medium"
    return "low — please verify columns manually"