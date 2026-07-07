"""
Seed script: Creates demo datasets + privacy assessments so the Privacy & Governance
page shows real data immediately after startup.

Run with:  python -m app.seed_privacy
           (from the backend/ directory)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import uuid

from app.core.database import SessionLocal, engine, Base
import app.models  # noqa: ensure all models are registered

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def _uuid():
    return str(uuid.uuid4())


def seed():
    from app.models.dataset import Dataset, DatasetVersion, Workspace, workspace_dataset
    from app.models.privacy import (
        PrivacyAssessment, SensitiveColumn, PIIDetection,
        DataClassification, ComplianceAssessment, RiskAssessment, GovernancePolicy,
    )

    # ── 1. Workspace ──────────────────────────────────────────────────────────
    ws = db.query(Workspace).filter(Workspace.id == "workspace-123").first()
    if not ws:
        ws = Workspace(id="workspace-123", name="Default Workspace")
        db.add(ws)
        db.commit()
        print("[OK] Workspace created")
    else:
        print("  Workspace already exists")

    # ── 2. Sample datasets ────────────────────────────────────────────────────
    sample_datasets = [
        {
            "id": "ds-customers-001",
            "name": "Customer Database",
            "description": "CRM export with PII fields",
            "status": "active",
            "owner_id": None,
        },
        {
            "id": "ds-transactions-002",
            "name": "Transaction Records",
            "description": "Payment history with financial data",
            "status": "active",
            "owner_id": None,
        },
        {
            "id": "ds-employees-003",
            "name": "Employee HR Data",
            "description": "HR records with sensitive fields",
            "status": "active",
            "owner_id": None,
        },
    ]

    for ds_data in sample_datasets:
        ds = db.query(Dataset).filter(Dataset.id == ds_data["id"]).first()
        if not ds:
            ds = Dataset(**ds_data, created_at=datetime.utcnow())
            db.add(ds)
            db.commit()
            # Link to workspace
            db.execute(
                workspace_dataset.insert().values(
                    workspace_id="workspace-123",
                    dataset_id=ds_data["id"]
                )
            )
            db.commit()
            print(f"[OK] Dataset '{ds_data['name']}' created + linked to workspace")
        else:
            print(f"  Dataset '{ds_data['name']}' already exists")

    # ── 3. DatasetVersions ────────────────────────────────────────────────────
    version_map = {
        "ds-customers-001":   "ver-customers-001-v1",
        "ds-transactions-002": "ver-transactions-002-v1",
        "ds-employees-003":   "ver-employees-003-v1",
    }

    for ds_id, ver_id in version_map.items():
        ver = db.query(DatasetVersion).filter(DatasetVersion.id == ver_id).first()
        if not ver:
            ver = DatasetVersion(
                id=ver_id,
                dataset_id=ds_id,
                version=1,
                original_filename="data.csv",
                stored_filename=f"{ds_id}/v1/data.csv",
                file_hash=_uuid(),
                file_size_bytes=1024 * 512,
                file_type="csv",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(ver)
        db.commit()
        print(f"  [OK] Version {ver_id} ensured")

    # ── 4. Privacy Assessments ────────────────────────────────────────────────
    privacy_data = [
        {
            "ver_id": "ver-customers-001-v1",
            "classification": {
                "overall_classification": "Highly Confidential",
                "contains_pii": True,
                "contains_financial": False,
                "contains_healthcare": False,
            },
            "compliance": {
                "gdpr_status": "Violations Found",
                "ccpa_status": "Violations Found",
                "hipaa_status": "Not Applicable",
                "pci_dss_status": "Not Applicable",
                "violations": [
                    "Email addresses stored unmasked",
                    "Phone numbers not encrypted",
                ],
                "recommendations": [
                    "Apply field-level encryption",
                    "Implement data masking pipeline",
                ],
            },
            "risk": {
                "privacy_risk_score": 82.0,
                "compliance_risk_score": 78.0,
                "business_risk_score": 65.0,
                "exposure_risk_score": 80.0,
                "overall_governance_score": 76.0,
            },
            "policy": {
                "data_owner": "Alice Chen",
                "steward": "Bob Martinez",
                "retention_policy": "Keep 30 Days",
                "access_policy": ["Admin", "Data Owner"],
                "sharing_policy": "Restricted",
            },
            "columns": [
                ("email",     "PII",           "Partial Mask", [("Email Address",  0.98, "Regex Match", 0.02)]),
                ("phone",     "PII",           "Partial Mask", [("Phone Number",   0.94, "Regex Match", 0.06)]),
                ("full_name", "PII",           "Hash",         [("Person Name",    0.87, "NLP Model",   0.13)]),
                ("address",   "PII",           "Full Mask",    [("Physical Address", 0.91, "NLP Model", 0.09)]),
            ],
        },
        {
            "ver_id": "ver-transactions-002-v1",
            "classification": {
                "overall_classification": "Confidential",
                "contains_pii": True,
                "contains_financial": True,
                "contains_healthcare": False,
            },
            "compliance": {
                "gdpr_status": "Compliant",
                "ccpa_status": "Compliant",
                "hipaa_status": "Not Applicable",
                "pci_dss_status": "Violations Found",
                "violations": ["Card numbers partially visible in logs"],
                "recommendations": ["Enforce PCI DSS tokenization"],
            },
            "risk": {
                "privacy_risk_score": 60.0,
                "compliance_risk_score": 55.0,
                "business_risk_score": 70.0,
                "exposure_risk_score": 58.0,
                "overall_governance_score": 60.0,
            },
            "policy": {
                "data_owner": "Carol Wang",
                "steward": "David Singh",
                "retention_policy": "Keep 90 Days",
                "access_policy": ["Admin", "Finance", "Auditor"],
                "sharing_policy": "Restricted",
            },
            "columns": [
                ("card_number", "Financial PII", "Full Mask", [("Credit Card",      0.99, "Luhn Check", 0.01)]),
                ("user_id",     "PII",           "Hash",      [("User Identifier",  0.75, "Context",    0.25)]),
            ],
        },
        {
            "ver_id": "ver-employees-003-v1",
            "classification": {
                "overall_classification": "Internal",
                "contains_pii": False,
                "contains_financial": False,
                "contains_healthcare": False,
            },
            "compliance": {
                "gdpr_status": "Compliant",
                "ccpa_status": "Not Applicable",
                "hipaa_status": "Not Applicable",
                "pci_dss_status": "Not Applicable",
                "violations": [],
                "recommendations": ["Maintain current masking practices"],
            },
            "risk": {
                "privacy_risk_score": 15.0,
                "compliance_risk_score": 12.0,
                "business_risk_score": 20.0,
                "exposure_risk_score": 14.0,
                "overall_governance_score": 15.0,
            },
            "policy": {
                "data_owner": "Eve Torres",
                "steward": "Frank Liu",
                "retention_policy": "Keep 1 Year",
                "access_policy": ["Admin", "HR", "Analyst"],
                "sharing_policy": "Internal",
            },
            "columns": [],
        },
    ]

    for pd in privacy_data:
        ver_id = pd["ver_id"]
        existing = db.query(PrivacyAssessment).filter(
            PrivacyAssessment.dataset_version_id == ver_id
        ).first()
        if existing:
            print(f"  Privacy assessment for {ver_id} already exists — skipping")
            continue

        assessment = PrivacyAssessment(
            dataset_version_id=ver_id,
            created_at=datetime.utcnow(),
        )
        db.add(assessment)
        db.flush()

        db.add(DataClassification(assessment_id=assessment.id, **pd["classification"]))

        comp = pd["compliance"]
        db.add(ComplianceAssessment(
            assessment_id=assessment.id,
            gdpr_status=comp["gdpr_status"],
            ccpa_status=comp["ccpa_status"],
            hipaa_status=comp["hipaa_status"],
            pci_dss_status=comp["pci_dss_status"],
            violations=comp["violations"],
            recommendations=comp["recommendations"],
        ))

        db.add(RiskAssessment(assessment_id=assessment.id, **pd["risk"]))

        pol = pd["policy"]
        db.add(GovernancePolicy(
            assessment_id=assessment.id,
            data_owner=pol["data_owner"],
            steward=pol["steward"],
            retention_policy=pol["retention_policy"],
            access_policy=pol["access_policy"],
            sharing_policy=pol["sharing_policy"],
        ))

        for col_name, level, mask, detections in pd["columns"]:
            sc = SensitiveColumn(
                assessment_id=assessment.id,
                schema_column_id=_uuid(),   # synthetic — no real schema column needed for demo
                column_name=col_name,
                classification_level=level,
                masking_recommendation=mask,
            )
            db.add(sc)
            db.flush()

            for entity_type, confidence, method, fp_prob in detections:
                db.add(PIIDetection(
                    sensitive_column_id=sc.id,
                    entity_type=entity_type,
                    confidence_score=confidence,
                    detection_method=method,
                    false_positive_probability=fp_prob,
                ))

        db.commit()
        print(f"[OK] Privacy assessment seeded for {ver_id}")

    db.close()
    print("\n[DONE] Seed complete. Privacy & Governance page is ready.")


if __name__ == "__main__":
    seed()
