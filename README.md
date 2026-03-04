# VeriCredit — Fraud & Credit Risk Governance Platform

**Course:** Risk and Fraud Analytics  
**Group:** Group 8  
**Institution:** IE University  
**Project Type:** Academic Group Project

---

# Overview

VeriCredit is a fraud detection and governance platform designed for digital lending workflows.

The system combines:

- Machine learning fraud detection
- Human-in-the-loop review
- Consensus decision mechanisms
- Cryptographic decision attestation

The goal of the platform is to reduce synthetic identity fraud and application fraud in digital lending while maintaining regulatory compliance and auditability.

---

# Project Team

Group 8 — Risk and Fraud Analytics

- Luiza Zinca
- Maria Bourbon
- Thi Tue Minh Do
- Thi Phuong Linh Do

---

# Problem Statement

Digital lenders face increasing exposure to synthetic identity fraud and automated application fraud.

Existing solutions typically focus on only one aspect of the problem:

- KYC verification
- Credit scoring
- Fraud detection

However, few systems provide end-to-end governance including:

- explainable AI decisions
- human oversight
- tamper-proof decision evidence

VeriCredit addresses this gap by introducing a layered fraud governance architecture.

---

# System Architecture

The platform follows a layered architecture composed of several major components.

### Data Layer
Collects signals from loan applications including:

- financial attributes
- behavioral telemetry
- device intelligence
- fraud pattern indicators

Examples of signals include typing entropy, mouse entropy, device risk, VPN usage, and application velocity.

---

### AI / ML Fraud Scoring Layer

Machine learning models analyze structured financial data and behavioral signals to estimate fraud probability.

The system outputs:

- fraud probability
- risk score
- explainable feature importance indicators

These outputs support transparent decision-making in financial workflows.

---

### Governance Layer

Decision policies determine the next step in the workflow.

Typical policy structure:

Low risk → Approve  
Medium risk → Human review  
High risk → Block

This ensures automated AI decisions remain governed and explainable.

---

### Human Review Layer

Borderline cases are escalated to fraud analysts.

Analysts provide:

- structured review scores
- investigation notes
- decision recommendations

Multiple reviewers may evaluate the same case.

---

### Consensus Layer

Reviewer decisions are aggregated using an Analytic Hierarchy Process (AHP).

This produces a consensus score and final decision while preventing individual reviewer bias.

---

### Blockchain Attestation Layer

Each finalized decision generates a tamper-evident evidence record.

The record includes:

- identity hash
- risk score
- final decision
- timestamp
- evidence hash

In production environments, this evidence can be anchored on blockchain to ensure immutable auditability.

---

# Demo Application

The project includes a Streamlit demo application simulating the VeriCredit fraud verification workflow.

The demo demonstrates:

1. AI fraud scoring
2. Governance rule evaluation
3. Human analyst review
4. Consensus decision aggregation
5. Cryptographic decision attestation

---

# Demo Workflow

Step 1 — AI Scoring  
The system analyzes application signals and produces a fraud probability score.

Step 2 — Pending Review Queue  
Borderline applications are placed in a human review queue.

Step 3 — Human Reviews  
Fraud analysts evaluate suspicious applications.

Step 4 — Consensus Decision  
Reviewer scores are aggregated using the AHP algorithm.

Step 5 — Oracle Attestation  
The system generates a cryptographic evidence record.

---

# Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Backend | Python |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas / NumPy |
| Consensus Algorithm | AHP |
| Cryptographic Evidence | Hash-based signatures |
| Version Control | Git / GitHub |

---

# Machine Learning Models

The fraud scoring engine uses supervised learning models trained on structured application data.

Models used in the MVP:

- Random Forest
- Logistic Regression

These models are suitable for tabular financial data and allow explainable predictions.

Future production versions may include:

- LightGBM
- XGBoost
- deep learning architectures

---

# Running the Demo

Install dependencies:

pip install -r requirements.txt

Run the Streamlit application:

streamlit run streamlit_app.py

Then open:

http://localhost:8501

---

# Example Fraud Signals

Financial signals:

- income
- credit history
- loan amount
- debt-to-income ratio

Behavioral signals:

- typing entropy
- mouse entropy

Device signals:

- device risk
- VPN usage

Fraud pattern indicators:

- application velocity
- fraud ring activity

---

# Governance and Compliance

VeriCredit is designed with regulatory considerations including:

- EU AI Act
- GDPR compliance
- explainable AI requirements

The architecture ensures:

- model transparency
- human oversight
- auditable decision records

---

# Repository Structure

VeriCredit/

├── 01_generate_synth_data.py  
├── 02_train_model.py  
├── 03_api_oracle.py  
├── streamlit_app.py  
├── ahp_engine.py  
├── artifacts/  
├── data/  
├── contracts/  
├── hardhat/  
├── requirements.txt  
└── README.md

---

# Future Improvements

Possible extensions of the system include:

- real-time API integration with banking platforms
- advanced fraud ring detection models
- blockchain smart contract registry
- reputation-based reviewer incentives
- large-scale ML model monitoring

---

# Project Status

Prototype / MVP

This repository demonstrates the core architecture and fraud governance workflow of the VeriCredit platform.

---

# License

This project is developed as an academic group project for the Risk and Fraud Analytics course.

For educational purposes only.

