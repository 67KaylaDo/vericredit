import json
import hmac
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
from joblib import load
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ahp_engine import ahp_consensus  # make sure file is in same folder

DB_PATH = "vericredit.db"
MODEL_PATH = "artifacts/model.joblib"
SCHEMA_PATH = "artifacts/feature_schema.json"

# MVP-only signing secret
ORACLE_SECRET = b"DEV_ONLY_CHANGE_ME"

# Review policy (governance knobs)
ESCALATION_LOW = 0.60
ESCALATION_HIGH = 0.80
AHP_BLOCK_THRESHOLD = 60.0         # if AHP score >= 60 => block
MIN_REVIEWS_FOR_CONSENSUS = 2      # require >=2 reviewers for AHP finalization

app = FastAPI(title="VeriCredit MVP API", version="1.0")

class ApplicationIn(BaseModel):
    applicant_id: str
    features: Dict[str, float]

class ScoreOut(BaseModel):
    applicant_id: str
    identity_hash: str
    risk_score: int
    probability: float
    threshold: float
    model_decision: str
    explanation_top: Dict[str, float]
    needs_human_review: bool

class AttestIn(BaseModel):
    identity_hash: str
    final_decision: str
    ai_risk_score: int
    ahp_score: Optional[float] = None
    evidence_payload: Dict[str, Any]

class AttestOut(BaseModel):
    evidence_hash: str
    oracle_signature: str
    issued_at: str

class ReviewIn(BaseModel):
    identity_hash: str
    reviewer: str
    review_score: int = Field(..., ge=1, le=9, description="1=approve ... 9=block")
    notes: Optional[str] = ""

class FinalizeOut(BaseModel):
    identity_hash: str
    ahp_score: float
    final_decision: str
    reviews_count: int

def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS cases (
        identity_hash TEXT PRIMARY KEY,
        created_at TEXT,
        ai_risk_score INTEGER,
        ai_probability REAL,
        model_threshold REAL,
        model_decision TEXT,
        needs_human INTEGER,
        final_decision TEXT,
        ahp_score REAL
      )
    """)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identity_hash TEXT,
        reviewer TEXT,
        review_score INTEGER,
        notes TEXT,
        created_at TEXT
      )
    """)
    conn.commit()
    return conn

CONN = connect_db()

with open(SCHEMA_PATH, "r") as f:
    SCHEMA = json.load(f)
FEATURES = SCHEMA["features"]
THRESHOLD = float(SCHEMA["threshold"])
MODEL = load(MODEL_PATH)

def stable_identity_hash(applicant_id: str, features: Dict[str, float]) -> str:
    canonical = {
        "applicant_id": applicant_id,
        "features": {k: float(features[k]) for k in sorted(features.keys())}
    }
    payload = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def model_explain_global() -> Dict[str, float]:
    clf = MODEL.named_steps["clf"]
    importances = getattr(clf, "feature_importances_", None)
    if importances is None:
        return {}
    pairs = sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True)[:6]
    return {k: float(v) for k, v in pairs}

def upsert_case(identity_hash: str, ai_risk_score: int, prob: float, model_decision: str, needs_human: bool):
    CONN.execute("""
      INSERT INTO cases(identity_hash, created_at, ai_risk_score, ai_probability, model_threshold,
                        model_decision, needs_human, final_decision, ahp_score)
      VALUES(?,?,?,?,?,?,?,?,?)
      ON CONFLICT(identity_hash) DO UPDATE SET
        ai_risk_score=excluded.ai_risk_score,
        ai_probability=excluded.ai_probability,
        model_threshold=excluded.model_threshold,
        model_decision=excluded.model_decision,
        needs_human=excluded.needs_human
    """, (
        identity_hash,
        datetime.now(timezone.utc).isoformat(),
        int(ai_risk_score),
        float(prob),
        float(THRESHOLD),
        model_decision,
        1 if needs_human else 0,
        None,
        None
    ))
    CONN.commit()

@app.post("/score", response_model=ScoreOut)
def score(app_in: ApplicationIn):
    missing = [f for f in FEATURES if f not in app_in.features]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing features: {missing}")

    x = pd.DataFrame([{f: float(app_in.features[f]) for f in FEATURES}])
    prob = float(MODEL.predict_proba(x)[:, 1][0])
    ai_risk_score = int(round(prob * 100))

    model_decision = "block" if prob >= THRESHOLD else "approve"
    needs_human = (ESCALATION_LOW <= prob <= ESCALATION_HIGH)

    identity_hash = stable_identity_hash(app_in.applicant_id, app_in.features)
    upsert_case(identity_hash, ai_risk_score, prob, model_decision, needs_human)

    return ScoreOut(
        applicant_id=app_in.applicant_id,
        identity_hash=identity_hash,
        risk_score=ai_risk_score,
        probability=prob,
        threshold=THRESHOLD,
        model_decision=model_decision,
        explanation_top=model_explain_global(),
        needs_human_review=needs_human
    )

@app.get("/cases/pending")
def pending_cases():
    cur = CONN.execute("""
      SELECT identity_hash, created_at, ai_risk_score, ai_probability, model_decision
      FROM cases
      WHERE needs_human=1 AND (final_decision IS NULL OR final_decision='')
      ORDER BY created_at ASC
      LIMIT 200
    """)
    rows = cur.fetchall()
    return [
        {
            "identity_hash": r[0],
            "created_at": r[1],
            "ai_risk_score": r[2],
            "ai_probability": r[3],
            "model_decision": r[4],
        }
        for r in rows
    ]

@app.get("/reviews/{identity_hash}")
def get_reviews(identity_hash: str):
    cur = CONN.execute("""
      SELECT reviewer, review_score, notes, created_at
      FROM reviews
      WHERE identity_hash=?
      ORDER BY created_at ASC
    """, (identity_hash,))
    rows = cur.fetchall()
    return [
        {"reviewer": r[0], "review_score": r[1], "notes": r[2], "created_at": r[3]}
        for r in rows
    ]

@app.post("/reviews/submit")
def submit_review(r: ReviewIn):
    # must exist as a case
    cur = CONN.execute("SELECT identity_hash FROM cases WHERE identity_hash=?", (r.identity_hash,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="Case not found. Score it first via /score.")

    CONN.execute("""
      INSERT INTO reviews(identity_hash, reviewer, review_score, notes, created_at)
      VALUES(?,?,?,?,?)
    """, (
        r.identity_hash,
        r.reviewer,
        int(r.review_score),
        r.notes or "",
        datetime.now(timezone.utc).isoformat()
    ))
    CONN.commit()
    return {"status": "ok"}

def compute_ahp_for_case(identity_hash: str) -> Optional[float]:
    cur = CONN.execute("""
      SELECT reviewer, identity_hash, review_score
      FROM reviews
      WHERE identity_hash=?
    """, (identity_hash,))
    rows = cur.fetchall()
    if not rows:
        return None

    df = pd.DataFrame(rows, columns=["reviewer", "identity_hash", "review_score"])
    scores = ahp_consensus(df, score_column="review_score")
    return float(scores.get(identity_hash))

@app.post("/cases/finalize", response_model=FinalizeOut)
def finalize_case(identity_hash: str):
    # count reviews
    cur = CONN.execute("SELECT COUNT(*) FROM reviews WHERE identity_hash=?", (identity_hash,))
    count = int(cur.fetchone()[0])

    if count < MIN_REVIEWS_FOR_CONSENSUS:
        raise HTTPException(status_code=400, detail=f"Need at least {MIN_REVIEWS_FOR_CONSENSUS} reviews to finalize.")

    ahp_score = compute_ahp_for_case(identity_hash)
    if ahp_score is None:
        raise HTTPException(status_code=400, detail="Could not compute AHP score.")

    final_decision = "block" if ahp_score >= AHP_BLOCK_THRESHOLD else "approve"

    CONN.execute("""
      UPDATE cases
      SET final_decision=?, ahp_score=?
      WHERE identity_hash=?
    """, (final_decision, float(ahp_score), identity_hash))
    CONN.commit()

    return FinalizeOut(
        identity_hash=identity_hash,
        ahp_score=float(ahp_score),
        final_decision=final_decision,
        reviews_count=count
    )

def oracle_sign(message_bytes: bytes) -> str:
    return hmac.new(ORACLE_SECRET, message_bytes, hashlib.sha256).hexdigest()

@app.post("/oracle/attest", response_model=AttestOut)
def attest(a: AttestIn):
    issued_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "identity_hash": a.identity_hash,
        "final_decision": a.final_decision,
        "ai_risk_score": int(a.ai_risk_score),
        "ahp_score": None if a.ahp_score is None else float(a.ahp_score),
        "evidence_payload": a.evidence_payload,
        "issued_at": issued_at
    }

    message = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    evidence_hash = hashlib.sha256(message).hexdigest()
    signature = oracle_sign(message)

    return AttestOut(evidence_hash=evidence_hash, oracle_signature=signature, issued_at=issued_at)