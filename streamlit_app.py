import os
import json
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="VeriCredit MVP Demo", layout="wide")
st.title("🏦 VeriCredit MVP Demo")
st.caption(f"Backend API: {API_URL}")

FEATURES = [
    "age","income","bureau_score","credit_history_months",
    "typing_entropy","mouse_entropy","device_risk","vpn_flag",
    "liveness_score","doc_quality","app_velocity","recent_ring_activity",
    "loan_amount","dti"
]

def post(path, payload=None, params=None):
    r = requests.post(f"{API_URL}{path}", json=payload, params=params, timeout=30)
    return r

def get(path, params=None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    return r

def show_kv(label, value):
    st.markdown(f"**{label}:** `{value}`")

# Sidebar
st.sidebar.header("Controls")
st.sidebar.write("Use this to run the full demo flow without Swagger.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["1) Score", "2) Pending", "3) Reviews", "4) Finalize (AHP)", "5) Oracle Attest"]
)

# ------------------ TAB 1: SCORE ------------------
with tab1:
    st.subheader("1) AI Scoring")
    colA, colB = st.columns([1.2, 1])

    presets = {
        "High risk": {
            "age": 29, "income": 32000, "bureau_score": 610, "credit_history_months": 12,
            "typing_entropy": 0.32, "mouse_entropy": 0.38, "device_risk": 0.78, "vpn_flag": 1,
            "liveness_score": 0.35, "doc_quality": 0.55, "app_velocity": 0.8, "recent_ring_activity": 0.65,
            "loan_amount": 18000, "dti": 0.55
        },
        "Borderline": {
            "age": 34, "income": 43000, "bureau_score": 650, "credit_history_months": 36,
            "typing_entropy": 0.50, "mouse_entropy": 0.52, "device_risk": 0.45, "vpn_flag": 0,
            "liveness_score": 0.62, "doc_quality": 0.70, "app_velocity": 0.35, "recent_ring_activity": 0.40,
            "loan_amount": 12000, "dti": 0.33
        },
        "Low risk": {
            "age": 40, "income": 52000, "bureau_score": 700, "credit_history_months": 48,
            "typing_entropy": 0.62, "mouse_entropy": 0.66, "device_risk": 0.18, "vpn_flag": 0,
            "liveness_score": 0.85, "doc_quality": 0.88, "app_velocity": 0.10, "recent_ring_activity": 0.12,
            "loan_amount": 9000, "dti": 0.22
        }
    }

    with colA:
        applicant_id = st.text_input("Applicant ID", value="A3001")
        preset = st.selectbox("Preset", ["Custom"] + list(presets.keys()))
        defaults = presets.get(preset, {})

        features = {}
        for f in FEATURES:
            if f == "vpn_flag":
                features[f] = st.number_input(f, value=int(defaults.get(f, 0)), step=1)
            else:
                features[f] = st.number_input(f, value=float(defaults.get(f, 0.0)))

        if st.button("🔍 Score via /score", type="primary"):
            payload = {"applicant_id": applicant_id, "features": features}
            r = post("/score", payload)
            if r.status_code == 200:
                out = r.json()
                st.session_state["score_out"] = out
                st.success("Scored successfully.")
            else:
                st.error(f"{r.status_code}: {r.text}")

    with colB:
        st.subheader("Latest Score Output")
        out = st.session_state.get("score_out")
        if out:
            st.json(out)
            show_kv("identity_hash", out.get("identity_hash"))
            show_kv("risk_score", out.get("risk_score"))
            show_kv("needs_human_review", out.get("needs_human_review"))
            st.session_state["active_identity_hash"] = out.get("identity_hash")
            st.session_state["active_ai_risk_score"] = out.get("risk_score")
        else:
            st.info("Run scoring to see output here.")

# ------------------ TAB 2: PENDING ------------------
with tab2:
    st.subheader("2) Pending Cases")
    if st.button("🔄 Refresh /cases/pending"):
        pass

    r = get("/cases/pending")
    if r.status_code != 200:
        st.error(f"{r.status_code}: {r.text}")
    else:
        pending = r.json()
        st.write(f"Pending cases: **{len(pending)}**")
        if pending:
            st.table(pending)
            options = [p["identity_hash"] for p in pending]
            selected = st.selectbox("Select identity_hash", options)
            st.session_state["active_identity_hash"] = selected
            st.success(f"Active identity_hash set: {selected}")
        else:
            st.info("No pending cases. (Either no borderlines or escalation band not triggering.)")

# ------------------ TAB 3: REVIEWS ------------------
with tab3:
    st.subheader("3) Submit Reviews")
    identity_hash = st.text_input("identity_hash", value=st.session_state.get("active_identity_hash",""))

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Existing reviews")
        if identity_hash:
            rr = get(f"/reviews/{identity_hash}")
            if rr.status_code == 200:
                reviews = rr.json()
                if reviews:
                    st.table(reviews)
                else:
                    st.info("No reviews yet for this case.")
            else:
                st.error(rr.text)
        else:
            st.info("Set an identity_hash first (from Score or Pending tab).")

    with col2:
        st.markdown("### Add a review")
        reviewer = st.text_input("Reviewer name", value="Analyst_1")
        review_score = st.slider("review_score (1 approve → 9 block)", 1, 9, 6)
        notes = st.text_area("Notes", value="Borderline signals, requesting more checks.")

        if st.button("✅ Submit /reviews/submit"):
            if not identity_hash:
                st.error("identity_hash is required")
            else:
                payload = {
                    "identity_hash": identity_hash,
                    "reviewer": reviewer,
                    "review_score": int(review_score),
                    "notes": notes
                }
                r = post("/reviews/submit", payload)
                if r.status_code == 200:
                    st.success("Review submitted.")
                else:
                    st.error(f"{r.status_code}: {r.text}")

# ------------------ TAB 4: FINALIZE ------------------
with tab4:
    st.subheader("4) Finalize (AHP consensus)")
    identity_hash = st.text_input("identity_hash (finalize)", value=st.session_state.get("active_identity_hash",""))

    if st.button("🏁 Finalize /cases/finalize", type="primary"):
        if not identity_hash:
            st.error("identity_hash is required")
        else:
            r = post("/cases/finalize", params={"identity_hash": identity_hash})
            if r.status_code == 200:
                out = r.json()
                st.session_state["final_out"] = out
                st.success("Finalized.")
            else:
                st.error(f"{r.status_code}: {r.text}")

    out = st.session_state.get("final_out")
    if out:
        st.json(out)
        st.session_state["active_final_decision"] = out.get("final_decision")
        st.session_state["active_ahp_score"] = out.get("ahp_score")
        show_kv("final_decision", out.get("final_decision"))
        show_kv("ahp_score", out.get("ahp_score"))

# ------------------ TAB 5: ORACLE ATTEST ------------------
with tab5:
    st.subheader("5) Oracle Attestation")
    identity_hash = st.text_input("identity_hash (attest)", value=st.session_state.get("active_identity_hash",""))
    final_decision = st.selectbox(
        "final_decision",
        ["approve","block"],
        index=1 if st.session_state.get("active_final_decision","block") == "block" else 0
    )

    ai_risk_score = st.number_input("ai_risk_score (0..100)", value=int(st.session_state.get("active_ai_risk_score", 50)))
    ahp_score = st.number_input("ahp_score (0..100)", value=float(st.session_state.get("active_ahp_score", 60.0)))

    payload_text = st.text_area(
        "evidence_payload (JSON)",
        value='{"model_version":"rf_v1","notes":"Streamlit oracle attestation"}',
        height=120
    )

    if st.button("🧾 Attest /oracle/attest", type="primary"):
        if not identity_hash:
            st.error("identity_hash is required")
        else:
            try:
                evidence_payload = json.loads(payload_text)
            except Exception:
                evidence_payload = {"raw": payload_text}

            payload = {
                "identity_hash": identity_hash,
                "final_decision": final_decision,
                "ai_risk_score": int(ai_risk_score),
                "ahp_score": float(ahp_score),
                "evidence_payload": evidence_payload
            }
            r = post("/oracle/attest", payload)
            if r.status_code == 200:
                out = r.json()
                st.session_state["attest_out"] = out
                st.success("Attestation created.")
            else:
                st.error(f"{r.status_code}: {r.text}")

    out = st.session_state.get("attest_out")
    if out:
        st.json(out)
        show_kv("evidence_hash", out.get("evidence_hash"))
        show_kv("oracle_signature", out.get("oracle_signature"))

        st.markdown("### Optional: Record on-chain (run in terminal)")
        st.code(
            "cd ~/vericredit-mvp/hardhat\n"
            "nvm use 20\n"
            "npx hardhat run scripts/record.js --network localhost\n",
            language="bash"
        )

