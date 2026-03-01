import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def generate_synthetic_applications(n=12000):
    # Time index (important for finance-style walk-forward split)
    start = pd.Timestamp("2024-01-01")
    ts = start + pd.to_timedelta(np.arange(n), unit="m")  # 1 app per minute

    age = RNG.integers(18, 75, size=n)
    income = np.clip(RNG.normal(42000, 18000, size=n), 8000, 250000)
    bureau_score = np.clip(RNG.normal(650, 70, size=n), 300, 850)
    credit_history_months = np.clip(RNG.normal(72, 48, size=n), 0, 420)

    # Behavioral & device signals
    typing_entropy = np.clip(RNG.normal(0.55, 0.12, size=n), 0.05, 1.0)
    mouse_entropy  = np.clip(RNG.normal(0.60, 0.15, size=n), 0.05, 1.0)
    device_risk = np.clip(RNG.beta(2, 8, size=n), 0, 1)
    vpn_flag = RNG.binomial(1, 0.12, size=n)

    # KYC quality signals
    liveness_score = np.clip(RNG.normal(0.78, 0.18, size=n), 0, 1)
    doc_quality    = np.clip(RNG.normal(0.80, 0.15, size=n), 0, 1)

    # Velocity / ring simulation
    ring_id = RNG.integers(0, 600, size=n)
    ring_size = pd.Series(ring_id).map(pd.Series(ring_id).value_counts()).values
    app_velocity = np.clip((ring_size / ring_size.max()), 0, 1)

    loan_amount = np.clip(RNG.normal(9000, 7000, size=n), 200, 80000)
    dti = np.clip(RNG.normal(0.28, 0.15, size=n), 0.01, 0.95)

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(ts),
        "age": age,
        "income": income,
        "bureau_score": bureau_score,
        "credit_history_months": credit_history_months,
        "typing_entropy": typing_entropy,
        "mouse_entropy": mouse_entropy,
        "device_risk": device_risk,
        "vpn_flag": vpn_flag,
        "liveness_score": liveness_score,
        "doc_quality": doc_quality,
        "app_velocity": app_velocity,
        "loan_amount": loan_amount,
        "dti": dti,
        "ring_id": ring_id,
    }).sort_values("timestamp").reset_index(drop=True)

    # Rolling “ops risk” signal (finance-style rolling features)
    df["recent_ring_activity"] = df["app_velocity"].rolling(120, min_periods=1).mean()

    # Synthetic fraud probability model
    z = (
        + 2.2 * (1 - df["liveness_score"])
        + 1.2 * (1 - df["doc_quality"])
        + 1.6 * df["device_risk"]
        + 0.9 * df["vpn_flag"]
        + 1.4 * df["app_velocity"]
        + 0.9 * df["recent_ring_activity"]
        + 0.8 * df["dti"]
        + 0.4 * (df["loan_amount"] / 80000.0)
        + 0.5 * (1 - df["typing_entropy"])
        + 0.3 * (1 - df["mouse_entropy"])
        + 0.6 * (1 - (df["credit_history_months"] / 420.0))
        + 0.5 * (1 - ((df["bureau_score"] - 300) / 550.0))
        - 0.2 * ((df["income"] - 8000) / (250000 - 8000))
    )

    p_fraud = sigmoid(z - 2.6)  # tune base rate
    df["is_synthetic_fraud"] = RNG.binomial(1, p_fraud.values).astype(int)

    delay_days = RNG.integers(7, 60, size=n)
    df["outcome_timestamp"] = df["timestamp"] + pd.to_timedelta(delay_days, unit="D")

    return df

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    df = generate_synthetic_applications(n=12000)
    df.to_csv("data/synthetic_credit_apps.csv", index=False)
    print("Saved data/synthetic_credit_apps.csv")
    print("Fraud rate:", df["is_synthetic_fraud"].mean())