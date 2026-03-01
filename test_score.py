import requests

API = "http://127.0.0.1:8000"

def send(applicant_id, features):
    r = requests.post(f"{API}/score", json={"applicant_id": applicant_id, "features": features})
    print(r.status_code, r.json())

send("A1001", {
  "age":29,"income":32000,"bureau_score":610,"credit_history_months":12,
  "typing_entropy":0.32,"mouse_entropy":0.38,"device_risk":0.78,"vpn_flag":1,
  "liveness_score":0.35,"doc_quality":0.55,"app_velocity":0.80,"recent_ring_activity":0.65,
  "loan_amount":18000,"dti":0.55
})

send("A1002", {
  "age":40,"income":52000,"bureau_score":700,"credit_history_months":48,
  "typing_entropy":0.62,"mouse_entropy":0.66,"device_risk":0.18,"vpn_flag":0,
  "liveness_score":0.85,"doc_quality":0.88,"app_velocity":0.10,"recent_ring_activity":0.12,
  "loan_amount":9000,"dti":0.22
})
