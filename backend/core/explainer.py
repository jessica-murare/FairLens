import shap
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


def safe_round(value, ndigits=4):
    if isinstance(value, list):
        return [safe_round(v, ndigits) for v in value]
    try:
        return round(float(value), ndigits)
    except Exception:
        return value

def compute_shap_explanation(df: pd.DataFrame, protected_col: str, target_col: str) -> dict:
    df = df.copy().dropna(subset=[protected_col, target_col])

    le = LabelEncoder()
    df[protected_col] = le.fit_transform(df[protected_col].astype(str))
    df[target_col] = le.fit_transform(df[target_col].astype(str))

    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c != target_col]

    X = df[feature_cols].fillna(0)
    y = df[target_col]

    X_train, X_test, y_train, _ = train_test_split(X, y, test_size=0.3, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    # SHAP linear explainer — fast for logistic regression
    explainer = shap.LinearExplainer(model, X_train, feature_perturbation="interventional")
    shap_values = explainer.shap_values(X_test[:200])  # sample 200 rows for speed

    # mean absolute SHAP per feature
    mean_shap = np.abs(shap_values).mean(axis=0)
    feature_importance = dict(zip(feature_cols, mean_shap.tolist()))
    feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

    # top 5 features
    top_features = list(feature_importance.items())[:5]

    # bias contribution — correlation of each feature with protected col
    bias_drivers = []
    for feat in feature_cols:
        corr = df[[feat, protected_col]].corr().iloc[0, 1]
        if abs(corr) > 0.1:
            bias_drivers.append({
                "feature": feat,
                "shap_importance": safe_round(feature_importance.get(feat, 0), 4),
                "protected_correlation": safe_round(corr, 4),
                "bias_risk": "HIGH" if abs(corr) > 0.3 else "MEDIUM"
            })

    bias_drivers = sorted(bias_drivers, key=lambda x: abs(x["protected_correlation"]), reverse=True)

    return {
        "top_features": [{"feature": k, "importance": safe_round(v, 4)} for k, v in top_features],
        "all_feature_importance": {k: safe_round(v, 4) for k, v in feature_importance.items()},
        "bias_drivers": bias_drivers[:5],
        "protected_column": protected_col,
        "summary": _shap_summary(bias_drivers, top_features)
    }

def _shap_summary(bias_drivers: list, top_features: list) -> str:
    if not bias_drivers:
        return "No strong feature-level bias drivers detected."
    top = bias_drivers[0]
    return (
        f"Feature '{top['feature']}' has the strongest correlation "
        f"({top['protected_correlation']}) with the protected attribute "
        f"and carries a {top['bias_risk']} bias risk."
    )