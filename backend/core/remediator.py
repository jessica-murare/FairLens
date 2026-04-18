import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from core.metrics import compute_fairness_metrics


def safe_round(value, ndigits=4):
    if isinstance(value, list):
        return [safe_round(v, ndigits) for v in value]
    try:
        return round(float(value), ndigits)
    except Exception:
        return value

def remediate(df: pd.DataFrame, protected_col: str, target_col: str) -> dict:
    
    # get before metrics first
    before = compute_fairness_metrics(df, protected_col, target_col)

    # apply reweighing
    reweighed_df = _reweigh(df, protected_col, target_col)
    after_reweigh = compute_fairness_metrics(reweighed_df, protected_col, target_col)

    # apply adversarial debiasing via fairness constraint
    after_constrained = _fairness_constrained_model(df, protected_col, target_col)

    # pick best result
    best = _pick_best(after_reweigh, after_constrained)

    return {
        "before": before,
        "after_reweighing": after_reweigh,
        "after_constrained": after_constrained,
        "best_method": best["method"],
        "best_result": best["result"],
        "improvement": _compute_improvement(before, best["result"])
    }

def _reweigh(df: pd.DataFrame, protected_col: str, target_col: str) -> pd.DataFrame:
    df = df.copy()
    le = LabelEncoder()
    df[protected_col] = le.fit_transform(df[protected_col].astype(str))
    df[target_col] = le.fit_transform(df[target_col].astype(str))

    total = len(df)
    group_counts = df.groupby([protected_col, target_col]).size()
    protected_counts = df.groupby(protected_col).size()
    target_counts = df.groupby(target_col).size()

    weights = []
    for _, row in df.iterrows():
        p = row[protected_col]
        t = row[target_col]
        expected = (protected_counts[p] / total) * (target_counts[t] / total)
        observed = group_counts.get((p, t), 1) / total
        weights.append(expected / (observed + 1e-9))

    df["sample_weight"] = weights
    df["sample_weight"] = df["sample_weight"].clip(0.1, 10.0)  # prevent extreme weights
    return df

def _fairness_constrained_model(df: pd.DataFrame, protected_col: str, target_col: str) -> dict:
    df = df.copy().dropna(subset=[protected_col, target_col])
    
    le = LabelEncoder()
    df[protected_col] = le.fit_transform(df[protected_col].astype(str))
    df[target_col] = le.fit_transform(df[target_col].astype(str))

    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c not in [target_col]]
    
    X = df[feature_cols].fillna(0)
    y = df[target_col]
    prot = df[protected_col]

    X_train, X_test, y_train, y_test, prot_train, prot_test = train_test_split(
        X, y, prot, test_size=0.3, random_state=42
    )

    # scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # penalize model for protected attribute correlation
    try:
        correlation_penalty = np.abs(np.corrcoef(
            X_train_scaled.T, prot_train
        )[-1, :-1])
        correlation_penalty = np.nan_to_num(correlation_penalty, nan=0.0, posinf=0.1, neginf=0.1)
    except:
        correlation_penalty = np.zeros(X_train_scaled.shape[1])
    
    feature_weights = 1.0 / (1.0 + correlation_penalty * 5)
    feature_weights = np.nan_to_num(feature_weights, nan=1.0, posinf=1.0, neginf=1.0)
    X_train_adjusted = X_train_scaled * feature_weights
    X_test_adjusted = X_test_scaled * feature_weights

    # ensure no NaN in final matrices
    X_train_adjusted = np.nan_to_num(X_train_adjusted, nan=0.0)
    X_test_adjusted = np.nan_to_num(X_test_adjusted, nan=0.0)

    model = LogisticRegression(max_iter=5000, solver='lbfgs', C=0.5)
    model.fit(X_train_adjusted, y_train)
    y_pred = model.predict(X_test_adjusted)

    test_df = X_test.copy()
    test_df[target_col] = y_test.values
    test_df["predicted"] = y_pred
    test_df[protected_col] = prot_test.values

    from core.metrics import _compute_fairness_scores
    group_metrics = {}
    for group_val, group_df in test_df.groupby(protected_col):
        actual = group_df[target_col]
        predicted = group_df["predicted"]
        tp = int(((predicted == 1) & (actual == 1)).sum())
        fp = int(((predicted == 1) & (actual == 0)).sum())
        fn = int(((predicted == 0) & (actual == 1)).sum())
        tn = int(((predicted == 0) & (actual == 0)).sum())
        group_metrics[str(group_val)] = {
            "count": int(len(group_df)),
            "positive_rate": float(safe_round(predicted.mean(), 4)),
            "tpr": float(safe_round(tp / (tp + fn + 1e-9), 4)),
            "fpr": float(safe_round(fp / (fp + tn + 1e-9), 4)),
            "accuracy": float(safe_round((predicted == actual).mean(), 4))
        }

    fairness = _compute_fairness_scores(group_metrics)
    return {
        "protected_column": protected_col,
        "target_column": target_col,
        "group_metrics": group_metrics,
        "fairness_scores": fairness,
        "model_accuracy": float(safe_round((y_pred == y_test.values).mean(), 4))
    }

def _pick_best(reweigh_result: dict, constrained_result: dict) -> dict:
    r_gap = reweigh_result["fairness_scores"].get("demographic_parity_gap", 999)
    c_gap = constrained_result["fairness_scores"].get("demographic_parity_gap", 999)
    
    if r_gap <= c_gap:
        return {"method": "reweighing", "result": reweigh_result}
    return {"method": "fairness_constrained_model", "result": constrained_result}

def _compute_improvement(before: dict, after: dict) -> dict:
    b = before["fairness_scores"]
    a = after["fairness_scores"]

    dp_before = float(b.get("demographic_parity_gap", 0))
    dp_after = float(a.get("demographic_parity_gap", 0))
    di_before = float(b.get("disparate_impact_ratio", 0))
    di_after = float(a.get("disparate_impact_ratio", 0))

    dp_improvement = round(((dp_before - dp_after) / (dp_before + 1e-9)) * 100, 1)
    di_improvement = round(((di_after - di_before) / (di_before + 1e-9)) * 100, 1)
    acc_before = float(before.get("model_accuracy", 0))
    acc_after = float(after.get("model_accuracy", 0))
    acc_change = round(((acc_after - acc_before) / (acc_before + 1e-9)) * 100, 1)

    return {
        "demographic_parity_gap_reduced_by": f"{dp_improvement}%",
        "disparate_impact_improved_by": f"{di_improvement}%",
        "accuracy_change": f"{acc_change}%",
        "verdict_before": str(b.get("bias_verdict", "UNKNOWN")),
        "verdict_after": str(a.get("bias_verdict", "UNKNOWN")),
        "success": bool(dp_after < dp_before)
    }