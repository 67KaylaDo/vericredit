import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    average_precision_score,
    precision_recall_curve,
    confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV

# ----------------------------
# VeriCredit feature contract
# ----------------------------
FEATURES = [
    "age", "income", "bureau_score", "credit_history_months",
    "typing_entropy", "mouse_entropy", "device_risk", "vpn_flag",
    "liveness_score", "doc_quality", "app_velocity", "recent_ring_activity",
    "loan_amount", "dti"
]
TARGET = "is_synthetic_fraud"

# ----------------------------
# Governance knobs (explicit)
# ----------------------------
TRAIN_RATIO = 0.70      # oldest
CALIB_RATIO = 0.15      # middle (probability calibration)
TEST_RATIO  = 0.15      # newest

PRECISION_TARGET = 0.80     # finance style: "if we block, be right"
FALLBACK_THRESHOLD = 0.50

CALIB_METHOD = "sigmoid"    # stable default

def time_three_split(df, train_ratio=0.70, calib_ratio=0.15):
    df = df.sort_values("timestamp").reset_index(drop=True)
    n = len(df)
    cut1 = int(n * train_ratio)
    cut2 = int(n * (train_ratio + calib_ratio))
    return df.iloc[:cut1].copy(), df.iloc[cut1:cut2].copy(), df.iloc[cut2:].copy()

def gini_from_auc(y_true, proba):
    return 2.0 * roc_auc_score(y_true, proba) - 1.0

def ks_statistic(y_true, proba):
    """
    Classic KS: max(|CDF_bad - CDF_good|) over sorted scores.
    """
    y_true = np.asarray(y_true).astype(int)
    proba = np.asarray(proba)

    order = np.argsort(proba)
    y = y_true[order]

    n_bad = y.sum()
    n_good = len(y) - n_bad
    if n_bad == 0 or n_good == 0:
        return 0.0

    cum_bad = np.cumsum(y) / n_bad
    cum_good = np.cumsum(1 - y) / n_good
    return float(np.max(np.abs(cum_bad - cum_good)))

def choose_threshold_precision_target(y_true, proba, precision_target=0.80, fallback=0.50):
    """
    Choose the LOWEST threshold that achieves precision >= target.
    (Same spirit as your current code, but cleaner + correct alignment.)
    """
    precision, recall, thresholds = precision_recall_curve(y_true, proba)

    chosen = None
    for p, t in zip(precision[:-1], thresholds):  # thresholds align with precision[:-1]
        if p >= precision_target:
            chosen = float(t)
            break

    return (float(fallback) if chosen is None else chosen), precision, recall, thresholds

def cutoff_scan(y_true, proba, cutoffs=(0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9)):
    """
    Like your creditcard notebook: show confusion-matrix-derived rates at different cutoffs.
    """
    out = []
    for c in cutoffs:
        preds = (proba >= c).astype(int)
        cm = confusion_matrix(y_true, preds)
        tn, fp, fn, tp = cm.ravel()
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        out.append({"cutoff": c, "TPR": tpr, "FPR": fpr, "TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn)})
    return out

def build_preprocessor():
    return ColumnTransformer([("num", StandardScaler(), FEATURES)], remainder="drop")

def train():
    df = pd.read_csv("data/synthetic_credit_apps.csv", parse_dates=["timestamp", "outcome_timestamp"])

    train_df, calib_df, test_df = time_three_split(df, TRAIN_RATIO, CALIB_RATIO)
    X_train, y_train = train_df[FEATURES], train_df[TARGET].astype(int)
    X_calib, y_calib = calib_df[FEATURES], calib_df[TARGET].astype(int)
    X_test,  y_test  = test_df[FEATURES],  test_df[TARGET].astype(int)

    pre = build_preprocessor()

    # ----------------------------
    # Model candidates (from notebooks ideas)
    # ----------------------------
    # 1) Logistic Regression (credit scoring standard)
    logreg = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(
            solver="liblinear",
            max_iter=2000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    # 2) Random Forest (fraud-ish non-linear)
    rf = Pipeline([
        ("pre", pre),
        ("clf", RandomForestClassifier(
            n_estimators=600,
            max_depth=10,
            min_samples_leaf=10,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42
        ))
    ])

    candidates = {
        "logreg": logreg,
        "rf": rf
    }

    results = {}
    best_name = None
    best_metric = -1.0

    # Fit each candidate, calibrate probabilities, evaluate on newest test slice
    for name, model in candidates.items():
        model.fit(X_train, y_train)

        # Probability calibration (helps your probabilities reach meaningful extremes)
        calibrated = CalibratedClassifierCV(estimator=model, method=CALIB_METHOD, cv="prefit")
        calibrated.fit(X_calib, y_calib)

        proba = calibrated.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, proba)
        pr_auc = average_precision_score(y_test, proba)
        gini = gini_from_auc(y_test, proba)
        ks = ks_statistic(y_test, proba)

        # pick best by PR-AUC (more relevant for imbalanced fraud)
        score_for_selection = pr_auc

        results[name] = {
            "auc": float(auc),
            "pr_auc": float(pr_auc),
            "gini": float(gini),
            "ks": float(ks),
            "proba_quantiles": {
                "p50": float(np.quantile(proba, 0.50)),
                "p75": float(np.quantile(proba, 0.75)),
                "p90": float(np.quantile(proba, 0.90)),
                "p95": float(np.quantile(proba, 0.95)),
                "p99": float(np.quantile(proba, 0.99)),
            }
        }

        if score_for_selection > best_metric:
            best_metric = score_for_selection
            best_name = name
            best_model = calibrated

    # Evaluate chosen model in more detail
    best_proba = best_model.predict_proba(X_test)[:, 1]

    chosen_threshold, precision, recall, thresholds = choose_threshold_precision_target(
        y_test, best_proba, PRECISION_TARGET, FALLBACK_THRESHOLD
    )
    preds = (best_proba >= chosen_threshold).astype(int)

    print("\n=== Best model selected ===")
    print("Best:", best_name, "| PR-AUC:", results[best_name]["pr_auc"], "| AUC:", results[best_name]["auc"])
    print("\n=== Classification Report @ chosen threshold ===")
    print(classification_report(y_test, preds))
    print("Chosen threshold (precision>=%.2f):" % PRECISION_TARGET, chosen_threshold)
    print("GINI:", gini_from_auc(y_test, best_proba))
    print("KS:", ks_statistic(y_test, best_proba))

    scan = cutoff_scan(y_test, best_proba)

    # Save artifacts
    Path("artifacts").mkdir(exist_ok=True)
    dump(best_model, "artifacts/model.joblib")

    schema = {
        "features": FEATURES,
        "target": TARGET,
        "threshold": float(chosen_threshold),
        "precision_target": float(PRECISION_TARGET),
        "selected_model": best_name,
        "calibration": {"method": CALIB_METHOD, "split": "time middle slice"},
        "splits": {"train_ratio": TRAIN_RATIO, "calib_ratio": CALIB_RATIO, "test_ratio": TEST_RATIO},
        "metrics_by_model": results,
        "cutoff_scan_test": scan
    }

    with open("artifacts/feature_schema.json", "w") as f:
        json.dump(schema, f, indent=2)

    print("\nSaved artifacts/model.joblib + artifacts/feature_schema.json")

if __name__ == "__main__":
    train()