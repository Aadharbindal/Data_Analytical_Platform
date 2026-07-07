import requests

def main():
    print("=== INTEGRATION TESTS ===")
    base = "http://localhost:8000"

    # 1. Health
    r = requests.get(base + "/api/v1/health", timeout=5)
    print("[1] Health:", r.status_code, r.json())

    # 2. Datasets list
    r = requests.get(base + "/api/v1/datasets?workspace_id=workspace-123", timeout=5)
    print("[2] Datasets list:", r.status_code, "count=" + str(len(r.json())))
    if r.ok and r.json():
        ds = r.json()[0]
        name = ds.get("name")
        status = ds.get("status")
        latest = ds.get("latest_version")
        print("    First dataset: name=" + str(name) + " status=" + str(status) + " latest_version=" + str(latest))

    # 3. Privacy report - customers
    r = requests.get(base + "/api/v1/privacy/ver-customers-001-v1/report", timeout=5)
    print("[3] Privacy report customers:", r.status_code)
    if r.ok:
        d = r.json()
        print("    risk_level=" + d["risk_level"] + " compliance=" + d["compliance_status"] + " pii_columns=" + str(len(d["pii_columns"])))
        cols = [c["column_name"] for c in d["pii_columns"]]
        print("    columns:", cols)
    else:
        print("    ERROR:", r.text[:300])

    # 4. Privacy report - transactions
    r = requests.get(base + "/api/v1/privacy/ver-transactions-002-v1/report", timeout=5)
    print("[4] Privacy report transactions:", r.status_code)
    if r.ok:
        d = r.json()
        print("    risk_level=" + d["risk_level"] + " pii_columns=" + str(len(d["pii_columns"])))

    # 5. Privacy report - employees (should have 0 PII)
    r = requests.get(base + "/api/v1/privacy/ver-employees-003-v1/report", timeout=5)
    print("[5] Privacy report employees:", r.status_code)
    if r.ok:
        d = r.json()
        print("    risk_level=" + d["risk_level"] + " pii_columns=" + str(len(d["pii_columns"])) + " (expected 0)")

    print("")
    print("=== ALL TESTS COMPLETE ===")

if __name__ == "__main__":
    main()

