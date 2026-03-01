import os
import requests
import streamlit as st

# If deployed, set API_URL in Streamlit secrets or environment variables
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="VeriCredit MVP", layout="wide")
st.title("🏦 VeriCredit MVP — AI Credit Risk + Human Consensus + Oracle Attestation")

st.caption(f"API URL: {API_URL}")

tab1, tab2, tab3, tab4 = st.tabs(["1) Score", "2) Pending & Reviews", "3) Finalize", "4) Oracle Attest"])

FEATURES = [
    "age","income","bureau_score","credit_history_months",
    "typing_entropy","mouse_entropy","device_risk","vpn_flag",
    "liveness_score","doc_quality","app_velocity","recent_ring_activity",
    "loan_amount","dti"
]

def api_post(path, payload=None, params=None):
    r = requests.post(f"{API_URL}{path}", json=payload, params=params, timeout=30)
    return r

def api_get(path, params=None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    return r

with tab1:
    st.subheader("Score a new application")
    colA, colB = st.columns([1.1, 1])

    with colA:
        applicant_id = st.text_input("Applicant ID", value="A3001")

        # Quick presets
        preset = st.selectbox("Preset", ["Custom", "High risk", "Borderline", "Low risk"])
        default = {}
        if preset == "High risk":
            default = {
                "age": 29, "income": 32000, "bureau_score": 610, "credit_history_months": 12,
                "typing_entropy": 0.32, "mouse_entropy": 0.38, "device_risk": 0.78, "vpn_flag": 1,
                "liveness_score": 0.35, "doc_quality": 0.55, "app_velocity": 0.80, "recent_ring_activity": 0.65,
                "loan_amount": 18000, "dti": 0.55
            }
        elif preset == "Borderline":
            default = {
                "age": 34, "income": 43000, "bureau_score": 650, "credit_history_months": 36,
                "typing_entropy": 0.50, "mouse_entropy": 0.52, "device_risk": 0.45, "vpn_flag": 0,
                "liveness_score": 0.62, "doc_quality": 0.70, "app_velocity": 0.35, "recent_ring_activity": 0.40,
                "loan_amount": 12000, "dti": 0.33
            }
        elif preset == "Low risk":
            default = {
                "age": 40, "income": 52000, "bureau_score": 700, "credit_history_months": 48,
                "typing_entropy": 0.62, "mouse_entropy": 0.66, "device_risk": 0.18, "vpn_flag": 0,
                "liveness_score": 0.85, "doc_quality": 0.88, "app_velocity": 0.10, "recent_ring_activity": 0.12,
                "loan_amount": 9000, "dti": 0.22
            }

        features = {}
        for f in FEATURES:
            val = default.get(f, 0.0)
            if f in ["vpn_flag"]:
                features[f] = st.number_input(f, value=int(val), step=1)
            else:
                features[f] = st.number_input(f, value=float(val))

        if st.button("🔍 Score via AI", type="primary"):
            payload = {"applicant_id": applicant_id, "features": features}
            r = api_post("/score", payload)
            if r.status_code == 200:
                out = r.json()
                st.session_state["last_score"] = out
                st.success("Scored successfully.")
            else:
                st.error(f"{r.status_code} {r.text}")

    with colB:
        st.subheader("Latest AI result")
        out = st.session_state.get("last_score")
        if out:
            st.json(out)
            st.write("Copy these for later steps:")
            st.code(f"identity_hash = {out['identity_hash']}")
            st.code(f"ai_risk_score = {out['risk_score']}")
        else:
            st.info("Run a score to see results here.")

with tab2:
    st.subheader("Pending cases & submit reviews")
    col1, col2 = st.columns([1.1, 1])

    with col1:
        if st.button("🔄 Refresh Pending"):
            pass

        r = api_get("/cases/pending")
        if r.status_code != 200:
            st.error(r.text)
            st.stop()

        pending = r.json()
        st.write(f"Pending cases: {len(pending)}")
        if not pending:
            st.info("No pending cases (your escalation band may be narrow).")
            st.stop()

        selected = st.selectbox("Select a case", [p["identity_hash"] for p in pending])
        st.session_state["selected_case"] = selected

        # Show existing reviews
        rr = api_get(f"/reviews/{selected}")
        if rr.status_code == 200:
            reviews = rr.json()
            st.write("Existing reviews")
            if reviews:
                st.table(reviews)
            else:
                st.write("No reviews yet.")
        else:
            st.error(rr.text)

    with col2:
        st.subheader("Submit review")
        identity_hash = st.session_state.get("selected_case", "")
        reviewer = st.text_input("Reviewer", value="Analyst_1")
        review_score = st.slider("Score (1=approve … 9=block)", 1, 9, 6)
        notes = st.text_area("Notes", value="")

        if st.button("✅ Submit Review"):
            payload = {
                "identity_hash": identity_hash,
                "reviewer": reviewer,
                "review_score": int(review_score),
                "notes": notes
            }
            r = api_post("/reviews/submit", payload)
            if r.status_code == 200:
                st.success("Review submitted.")
            else:
                st.error(r.text)

with tab3:
    st.subheader("Finalize case (AHP consensus)")
    identity_hash = st.text_input("Identity Hash", value=st.session_state.get("selected_case", ""))

    if st.button("🏁 Finalize via AHP"):
        r = api_post("/cases/finalize", params={"identity_hash": identity_hash})
        if r.status_code == 200:
            out = r.json()
            st.session_state["finalized"] = out
            st.success("Finalized.")
            st.json(out)
            st.code(f"ahp_score = {out['ahp_score']}")
            st.code(f"final_decision = {out['final_decision']}")
        else:
            st.error(r.text)

with tab4:
    st.subheader("Oracle attestation (evidence hash + signature)")
    scored = st.session_state.get("last_score", {})
    finalized = st.session_state.get("finalized", {})

    identity_hash = st.text_input("identity_hash", value=finalized.get("identity_hash", scored.get("identity_hash", "")))
    ai_risk_score = st.number_input("ai_risk_score (0..100)", value=int(scored.get("risk_score", 50)))
    ahp_score = st.number_input("ahp_score (0..100)", value=float(finalized.get("ahp_score", 60.0)))
    final_decision = st.selectbox("final_decision", ["approve", "block"],
                                 index=1 if finalized.get("final_decision", "block") == "block" else 0)

    evidence_payload = st.text_area(
        "evidence_payload (JSON-like text ok for MVP)",
        value='{"model_version":"rf_v1","notes":"Streamlit UI attestation"}'
    )

    if st.button("🧾 Create Attestation"):
        try:
            # convert payload string to dict safely in MVP (simple)
            import json
            payload_dict = json.loads(evidence_payload)
        except Exception:
            payload_dict = {"raw": evidence_payload}

        payload = {
            "identity_hash": identity_hash,
            "final_decision": final_decision,
            "ai_risk_score": int(ai_risk_score),
            "ahp_score": float(ahp_score),
            "evidence_payload": payload_dict
        }

        r = api_post("/oracle/attest", payload)
        if r.status_code == 200:
            out = r.json()
            st.success("Attested.")
            st.json(out)
            st.code(f"evidence_hash = {out['evidence_hash']}")
            st.code(f"oracle_signature = {out['oracle_signature']}")
        else:
            st.error(r.text)
            
