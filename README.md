# 🏦 VeriCredit — AI + Human Consensus + Blockchain for Financial & Credit Risk

VeriCredit is a Financial & Credit Risk verification platform that combines:

- 🤖 AI/ML credit risk scoring  
- 👩‍⚖️ Human-in-the-loop consensus (AHP-based)  
- 🔐 Cryptographic oracle attestation  
- ⛓ Blockchain anchoring for auditability  

The system is designed to reduce fraud, improve explainability, and provide tamper-proof decision logs across the EU financial ecosystem.

---

# 🚨 Problem

Financial institutions face increasing:

- Synthetic identity fraud  
- Application manipulation  
- Model opacity & explainability issues  
- Regulatory pressure (EU AI Act, GDPR)  
- Lack of immutable audit trails  

AI models alone are not enough.  
Human-only review is slow and expensive.  
Traditional systems lack tamper-proof evidence.

---

# 💡 Solution: VeriCredit

VeriCredit introduces a hybrid architecture:

1. AI model generates risk score + explanation  
2. Borderline cases escalate to human reviewers  
3. AHP consensus aggregates human judgments  
4. Oracle generates cryptographic evidence hash  
5. Smart contract anchors decision on-chain  

This creates:

- Transparent risk scoring  
- Human oversight  
- Immutable audit records  
- Compliance-ready traceability  

---

# 🏗 System Architecture

User → Streamlit UI  
        ↓  
FastAPI Backend (AI + AHP + Oracle)  
        ↓  
Evidence Hash  
        ↓  
EVM Smart Contract (VeriCreditRegistry)  

---

# 📂 Project Structure

vericredit-mvp/

- 01_generate_synth_data.py  
- 02_train_model.py  
- 03_api_oracle.py  
- 05_ahp_engine.py  
- streamlit_app.py  
- artifacts/  
- hardhat/  
  - contracts/VeriCreditRegistry.sol  
  - scripts/  

---

# ⚙️ How It Works (Step-by-Step)

## 1️⃣ Generate Synthetic Data

python 01_generate_synth_data.py

## 2️⃣ Train ML Model

python 02_train_model.py

Produces:
- artifacts/model.joblib  
- artifacts/feature_schema.json  

## 3️⃣ Run API Backend

python -m uvicorn 03_api_oracle:app --reload --port 8000

Swagger UI:
http://127.0.0.1:8000/docs

## 4️⃣ Run Streamlit UI

streamlit run streamlit_app.py

Streamlit UI:
http://localhost:8501

## 5️⃣ Deploy Smart Contract (Local)

cd hardhat  
nvm use 20  
npx hardhat node  

Deploy:
npx hardhat run scripts/deploy.js --network localhost  

Record verification:
npx hardhat run scripts/record.js --network localhost  

---

# 🔐 Smart Contract: VeriCreditRegistry

Stores:

- identity_hash  
- ai_risk_score  
- ahp_score  
- humanConsensusUsed  
- evidence_hash  
- timestamp  
- reporter address  

This ensures immutable, auditable decision logs.

---

# 📊 Example Flow

1. User submits loan application  
2. AI returns risk score (e.g., 67/100)  
3. Borderline → Human review  
4. AHP consensus returns 70  
5. Oracle hashes evidence payload  
6. Smart contract stores verification record  

---

# 🎯 Market Opportunity

Target clients:

- Banks  
- Digital lenders  
- InsurTech companies  
- FinTech platforms  
- RegTech providers  

Revenue Model:

- SaaS subscription  
- API usage pricing  
- Compliance verification fees  
- B2B institutional licensing  

---

# 💶 €1M Funding Allocation (12–18 Months)

AI/ML Engineering – €250k  
Blockchain Development – €200k  
Backend & Infrastructure – €200k  
EU Compliance (AI Act / GDPR) – €150k  
Data acquisition – €100k  
Pilot deployments – €100k  

---

# 🚀 Next Steps

- Deploy API to cloud (Render / Railway)  
- Deploy Streamlit UI to Streamlit Cloud  
- Move smart contract to testnet (Sepolia)  
- Add real-world credit bureau integrations  
- Add model explainability dashboards (SHAP)  

---

# 👩‍💻 Author

Kayla Do  
Financial & Credit Risk — AI + Blockchain MVP  

---

# ⚠️ Disclaimer

This MVP uses synthetic data for academic and demonstration purposes.

