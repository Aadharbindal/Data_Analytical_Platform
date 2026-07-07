"""
Seed script: Creates deterministic dummy data for Catalog, Insights, and Recommendations
so the enterprise modules show real data immediately after startup.

Run with:  python -m app.seed_analytics
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import uuid

from app.core.database import SessionLocal, engine, Base
import app.models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def _uuid():
    return str(uuid.uuid4())

def seed():
    from app.models.dataset import Dataset, DatasetVersion
    from app.models.catalog import MetadataCatalog, CatalogEntry, DatasetTag, DatasetDocumentation, CatalogScore
    from app.models.insight import Insight, InsightScore, InsightRanking
    from app.models.recommendation import Recommendation, RecommendationScore, RecommendationEvidence

    # Verify datasets exist (run seed_privacy first if needed)
    datasets = db.query(Dataset).all()
    if not datasets:
        print("[ERROR] No datasets found. Please run seed_privacy.py first.")
        return

    # ── 1. Catalog ────────────────────────────────────────────────────────────
    for ds in datasets:
        cat = db.query(MetadataCatalog).filter(MetadataCatalog.dataset_id == ds.id).first()
        if not cat:
            cat = MetadataCatalog(
                id=_uuid(),
                dataset_id=ds.id,
                dataset_version_id=db.query(DatasetVersion).filter(DatasetVersion.dataset_id == ds.id).first().id,
                last_indexed_at=datetime.utcnow()
            )
            db.add(cat)
            db.flush()

            # Documentation
            doc = DatasetDocumentation(
                catalog_id=cat.id,
                business_summary=f"Core dataset for {ds.name}. Contains essential operational metrics.",
                technical_summary=f"Auto-ingested {ds.name} with standard normalization.",
                recommended_kpis=["Volume", "Growth Rate"]
            )
            db.add(doc)

            # Score
            score = CatalogScore(
                catalog_id=cat.id,
                popularity_score=85.0,
                freshness_score=92.0,
                quality_score=98.0,
                trust_score=90.0,
                ai_readiness_score=88.0
            )
            db.add(score)

            # Entries (column count, etc)
            col_count = 4 if "customer" in ds.name.lower() else (2 if "transaction" in ds.name.lower() else 10)
            db.add(CatalogEntry(catalog_id=cat.id, category="Schema", key="column_count", value=col_count))
            
            # Tags
            db.add(DatasetTag(catalog_id=cat.id, tag_name="Production", tag_type="Auto"))
            db.add(DatasetTag(catalog_id=cat.id, tag_name="Verified", tag_type="Governance"))

            db.commit()
            print(f"[OK] Catalog seeded for dataset {ds.name}")
        else:
            print(f"  Catalog for {ds.name} already exists")

    # ── 2. Insights ───────────────────────────────────────────────────────────
    ver_ids = ["ver-customers-001-v1", "ver-transactions-002-v1", "ver-employees-003-v1"]
    
    insight_data = [
        {
            "dataset_version_id": "ver-transactions-002-v1",
            "title": "Unusual Spike in Weekend Transactions",
            "category": "ANOMALY",
            "insight_type": "SUDDEN_GROWTH",
            "metric": "Transaction Volume",
            "metric_value": 45000,
            "severity": "HIGH",
            "confidence": 0.94,
            "final_score": 92.5
        },
        {
            "dataset_version_id": "ver-customers-001-v1",
            "title": "High Churn Risk in Enterprise Segment",
            "category": "RISK",
            "insight_type": "CHURN_PREDICTION",
            "metric": "Churn Probability",
            "metric_value": 0.35,
            "severity": "CRITICAL",
            "confidence": 0.88,
            "final_score": 89.0
        },
        {
            "dataset_version_id": "ver-employees-003-v1",
            "title": "Engineering Headcount Trending Below Target",
            "category": "TREND",
            "insight_type": "VARIANCE",
            "metric": "Headcount Gap",
            "metric_value": -12,
            "severity": "MEDIUM",
            "confidence": 0.99,
            "final_score": 75.0
        },
        {
            "dataset_version_id": "ver-transactions-002-v1",
            "title": "New Upsell Opportunity Identified in EU Region",
            "category": "OPPORTUNITY",
            "insight_type": "SEGMENT_DISCOVERY",
            "metric": "Potential ARR",
            "metric_value": 120000,
            "severity": "LOW",
            "confidence": 0.81,
            "final_score": 85.0
        }
    ]

    for data in insight_data:
        existing = db.query(Insight).filter(
            Insight.dataset_version_id == data["dataset_version_id"],
            Insight.title == data["title"]
        ).first()
        
        if existing:
            print(f"  Insight '{data['title']}' already exists")
            continue

        insight = Insight(
            dataset_version_id=data["dataset_version_id"],
            title=data["title"],
            category=data["category"],
            insight_type=data["insight_type"],
            metric=data["metric"],
            severity=data["severity"],
            status="VALIDATED"
        )
        db.add(insight)
        db.flush()

        db.add(InsightScore(
            insight_id=insight.id,
            confidence=data["confidence"],
            business_impact=0.8,
            urgency=0.9,
            novelty=0.7
        ))
        
        db.add(InsightRanking(
            insight_id=insight.id,
            final_score=data["final_score"]
        ))
        
        db.commit()
        print(f"[OK] Insight seeded: {data['title']}")


    # ── 3. Recommendations ────────────────────────────────────────────────────
    recommendation_data = [
        {
            "dataset_version_id": "ver-transactions-002-v1",
            "title": "Implement Dynamic Pricing on Weekends",
            "description": "Based on the consistent weekend transaction volume spikes, we recommend enabling dynamic pricing to capture additional margin.",
            "business_domain": "SALES",
            "category": "REVENUE_GROWTH",
            "priority": "HIGH",
            "roi_estimate": 45000.0,
            "confidence": 0.89
        },
        {
            "dataset_version_id": "ver-customers-001-v1",
            "title": "Launch Targeted Retention Campaign for Enterprise",
            "description": "Enterprise churn risk is elevated. Deploy dedicated CSM resources and exclusive retention offers immediately.",
            "business_domain": "CUSTOMER_SUCCESS",
            "category": "RISK_MITIGATION",
            "priority": "CRITICAL",
            "roi_estimate": 120000.0,
            "confidence": 0.92
        },
        {
            "dataset_version_id": "ver-employees-003-v1",
            "title": "Accelerate Engineering Hiring Pipeline",
            "description": "Open 3 new requisitions and increase referral bonuses to close the 12 headcount gap before Q3.",
            "business_domain": "HR",
            "category": "OPERATIONAL_EFFICIENCY",
            "priority": "MEDIUM",
            "roi_estimate": 0.0,
            "confidence": 0.95
        }
    ]

    for data in recommendation_data:
        existing = db.query(Recommendation).filter(
            Recommendation.dataset_version_id == data["dataset_version_id"],
            Recommendation.title == data["title"]
        ).first()
        
        if existing:
            print(f"  Recommendation '{data['title']}' already exists")
            continue

        # Create dummy decision ID since it's a non-nullable foreign key
        dummy_decision_id = _uuid()
        
        rec = Recommendation(
            dataset_version_id=data["dataset_version_id"],
            decision_id=dummy_decision_id, # Just a placeholder since we are bypassing the decision layer for seed
            title=data["title"],
            description=data["description"],
            business_domain=data["business_domain"],
            category=data["category"],
            priority=data["priority"],
            roi_estimate=data["roi_estimate"],
            confidence=data["confidence"],
            status="APPROVED"
        )
        db.add(rec)
        db.flush()
        db.commit()
        print(f"[OK] Recommendation seeded: {data['title']}")

    db.close()
    print("\n[DONE] Analytics Seed complete. Catalog, Insights, and Recommendations are ready.")

if __name__ == "__main__":
    seed()
