import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from itertools import combinations
from sklearn.model_selection import train_test_split


def safe_round(value, ndigits=4):
    if isinstance(value, list):
        return [safe_round(v, ndigits) for v in value]
    try:
        return round(float(value), ndigits)
    except Exception:
        return value

def compute_fairness_metrics(df: pd.DataFrame, protected_col: str, target_col: str) -> dict:
    df = df.copy().dropna(subset=[protected_col, target_col])
    
    le = LabelEncoder()
    df[protected_col] = le.fit_transform(df[protected_col].astype(str))
    df[target_col] = le.fit_transform(df[target_col].astype(str))

    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c not in [target_col]]
    
    X = df[feature_cols].fillna(0)
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    test_df = X_test.copy()
    test_df[target_col] = y_test.values
    test_df["predicted"] = y_pred
    test_df[protected_col] = df.loc[X_test.index, protected_col].values

    groups = test_df.groupby(protected_col)
    metrics_per_group = {}

    for group_val, group_df in groups:
        actual = group_df[target_col]
        predicted = group_df["predicted"]
        tp = ((predicted == 1) & (actual == 1)).sum()
        fp = ((predicted == 1) & (actual == 0)).sum()
        fn = ((predicted == 0) & (actual == 1)).sum()
        tn = ((predicted == 0) & (actual == 0)).sum()

        metrics_per_group[str(group_val)] = {
            "count": len(group_df),
            "positive_rate": safe_round(predicted.mean(), 4),
            "tpr": safe_round(tp / (tp + fn + 1e-9), 4),   # true positive rate
            "fpr": safe_round(fp / (fp + tn + 1e-9), 4),   # false positive rate
            "accuracy": safe_round((predicted == actual).mean(), 4)
        }

    return {
        "protected_column": protected_col,
        "target_column": target_col,
        "group_metrics": metrics_per_group,
        "fairness_scores": _compute_fairness_scores(metrics_per_group),
        "model_accuracy": safe_round((y_pred == y_test.values).mean(), 4)
    }

def _compute_fairness_scores(group_metrics: dict) -> dict:
    groups = list(group_metrics.values())
    if len(groups) < 2:
        return {"error": "Need at least 2 groups"}

    pos_rates = [g["positive_rate"] for g in groups]
    tprs = [g["tpr"] for g in groups]
    fprs = [g["fpr"] for g in groups]

    # Demographic parity gap (ideal = 0)
    dp_gap = round(max(pos_rates) - min(pos_rates), 4)

    # Equalized odds gap (ideal = 0)
    tpr_gap = round(max(tprs) - min(tprs), 4)
    fpr_gap = round(max(fprs) - min(fprs), 4)

    # Disparate impact ratio (ideal = 1.0, <0.8 = biased)
    di_ratio = round(min(pos_rates) / (max(pos_rates) + 1e-9), 4)

    return {
        "demographic_parity_gap": dp_gap,
        "equalized_odds_tpr_gap": tpr_gap,
        "equalized_odds_fpr_gap": fpr_gap,
        "disparate_impact_ratio": di_ratio,
        "bias_verdict": _verdict(dp_gap, di_ratio)
    }

def _verdict(dp_gap: float, di_ratio: float) -> str:
    if di_ratio < 0.8 or dp_gap > 0.1:
        return "BIASED"
    elif dp_gap > 0.05:
        return "MODERATE BIAS"
    return "FAIR"


def compute_intersectional_bias(df: pd.DataFrame, protected_cols: list, target_col: str) -> dict:
    df = df.copy().dropna(subset=protected_cols + [target_col])
    
    le = LabelEncoder()
    df[target_col] = le.fit_transform(df[target_col].astype(str))
    
    # encode all protected cols
    for col in protected_cols:
        df[col] = df[col].astype(str)

    results = {}

    # single attribute analysis
    for col in protected_cols:
        groups = df.groupby(col)["predicted" if "predicted" in df.columns else target_col]
        pos_rates = {}
        for name, grp in df.groupby(col):
            pos_rates[str(name)] = round(grp[target_col].mean(), 4)
        results[col] = {
            "type": "single",
            "positive_rates": pos_rates,
            "gap": safe_round(max(pos_rates.values()) - min(pos_rates.values()), 4)
        }

    # pairwise intersectional analysis
    for col_a, col_b in combinations(protected_cols, 2):
        key = f"{col_a} x {col_b}"
        df["_intersect"] = df[col_a] + " + " + df[col_b]
        group_rates = {}
        
        for name, grp in df.groupby("_intersect"):
            if len(grp) >= 10:  # skip tiny groups
                group_rates[str(name)] = {
                    "count": len(grp),
                    "positive_rate": safe_round(grp[target_col].mean(), 4)
                }

        if group_rates:
            rates = [v["positive_rate"] for v in group_rates.values()]
            results[key] = {
                "type": "intersectional",
                "groups": group_rates,
                "gap": safe_round(max(rates) - min(rates), 4),
                "most_privileged": max(group_rates, key=lambda k: group_rates[k]["positive_rate"]),
                "most_disadvantaged": min(group_rates, key=lambda k: group_rates[k]["positive_rate"]),
                "bias_verdict": "BIASED" if (max(rates) - min(rates)) > 0.1 else "FAIR"
            }

    return {
        "protected_columns": protected_cols,
        "target_column": target_col,
        "intersectional_analysis": results,
        "summary": _intersectional_summary(results)
    }

def _intersectional_summary(results: dict) -> dict:
    biased = [k for k, v in results.items() if v.get("bias_verdict") == "BIASED" or v.get("gap", 0) > 0.1]
    worst = max(results.items(), key=lambda x: x[1].get("gap", 0))
    return {
        "biased_combinations": biased,
        "worst_combination": worst[0],
        "worst_gap": worst[1].get("gap", 0)
    }
