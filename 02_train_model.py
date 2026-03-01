import json
from pathlib import Path
import pandas as pd
import numpy as np
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
from sklearn.ensemble import RandomForestClassifier

FEATURES = [
    "age", "income", "bureau_score", "credit_history_months",
    "typing_entropy", "mouse_entropy", "device_risk", "vpn_flag",
    "liveness_score", "doc_quality", "app_velocity", "recent_ring_activity",
    "loan_amount", "dti"
]
TARGET = "is_synthetic_fraud"

def time_split(df, train_ratio=0.75):
    df = df.sort_values("timestamp").reset_index(drop=True)
    cut = int(len(df) * train_ratio)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()

def train():
    df = pd.read_csv("data/synthetic_credit_apps.csv", parse_dates=["timestamp", "outcome_timestamp"])
    train_df, test_df = time_split(df, 0.75)

    X_train, y_train = train_df[FEATURES], train_df[TARGET].astype(int)
    X_test,  y_test  = test_df[FEATURES],  test_df[TARGET].astype(int)

    pre = ColumnTransformer([("num", StandardScaler(), FEATURES)], remainder="drop")

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        random_state=42,
        class_weight="balanced_subsample"
    )

    pipe = Pipeline([("pre", pre), ("clf", clf)])
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)

    print("\n=== Classification Report (time split) ===")
    print(classification_report(y_test, preds))
    print("ROC-AUC:", roc_auc_score(y_test, proba))

    # Finance-style: choose threshold like a “strategy parameter”
    precision, recall, thresholds = precision_recall_curve(y_test, proba)
    chosen = 0.5
    for p, t in zip(precision, np.r_[thresholds, 1.0]):
        if p >= 0.80:
            chosen = float(t)
            break
    print("Chosen threshold (precision>=0.80):", chosen)

    Path("artifacts").mkdir(exist_ok=True)
    dump(pipe, "artifacts/model.joblib")

    schema = {
        "features": FEATURES,
        "target": TARGET,
        "threshold": chosen,
        "model": "RandomForestClassifier",
        "train_ratio_time_split": 0.75
    }
    with open("artifacts/feature_schema.json", "w") as f:
        json.dump(schema, f, indent=2)

    print("Saved artifacts/model.joblib + artifacts/feature_schema.json")

if __name__ == "__main__":
    train()